#!/bin/usr/env python3
# -*- coding: utf-8 -*-

import asyncio, logging
import aiomysql

async def create_pool(loop, **kw):
    logging.info('Creating a global connect pool...')
    global conPool
    conPool = await aiomysql.create_pool(
            host = kw.get('host', 'localhost'),
            port = kw.get('port', '3306'),
            user = kw['user'],
            password = kw['password'],
            db = kw['db'],
            charset = kw.get('charset', 'utf8'),
            autocommit = kw.get('autocommit', True),
            maxsize = kw.get('maxsize', 10),
            minsize = kw.get('minsize', 1),
            loop = loop
    )

def log(sql, args=()):
    logging.info('SQL: %s, args: %s' % (sql, args))

async def select_wrap(sql, args, size = None):
    log(sql, args)
    async with conPool.get() as con:
        async with con.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql.replace('?', '%'), args or ())
            if size:
                rs = await cursor.fetchmany(size)
            else:
                rs = await cursor.fetchall()
        '感觉这里可以在connect之后做'
        logging.info('rows return %s' % len(rs))
        return rs

async def execute_wrap(sql, args, autocommit = True):
    log(sql, args)
    async with conPool.get() as con:
        if not autocommit:
            await con.begin()

        try:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%'), args)
                rs = cur.rowcount

            if not autocommit:
                await con.commit()

        except BaseException as e:
            if not autocommit:
                await con.rollback()
            raise

        return rs

class Field(object):
    'The base class of all table column'
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s: %s>' % (self__class__.__name__, self.column_type, self.name)

class StringField(Field):
    'StringField inheritance from Field'
    def __init__(self, name = None, primary_key = False, default = None, ddl = 'varchar(100)'):
        super.__init__(name, ddl, primary_key, default)

class BooleanField(Field):
    'BooleanField inheritance from Field'
    def __init__(self, name = None, default = None):
        super.__init__(name, 'boolean', False, default)

class IntegerField(Field):
    'IntegerField inheritance from Field'
    def __init__(self, name = None, primary_key = False, default = None):
        super.__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    'FloatField inheritance from Field'
    def __init__(self, name = None, primary_key = False, default = None):
        super.__init__(name, 'real', primary_key, default)

class TextField(Field):
    'TextField inheritance from Field'
    def __init__(self, name = None, default = None):
        super.__init__(name, 'text', False, default)

def create_args_str(num):
    tl = []
    for i in range(num):
        tl.append('?')
    return ', '.join(tl)

class ModelMetaclass(type):
    
    def __new__(cls, name, base, attrs):
        if name == 'Model':
            return type.__new__(cls, name, base, attrs)

        tablename = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tablename))
        mappings = dict()
        fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(k, Field):
                logging.info('  found mapping: %s==>%s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise StandardError('Duplicate primary key for field: %s' % k)
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise StandardError('Primary key not found')
        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = list(map(lambda f: '`%s`' % f, fields))

        attrs[__mappings__] = mappings
        attrs[__table__] = tablename
        attrs[__primary_key__] = primary_key
        attrs[__fields__] = fields
        attrs[__select__] = 'select `%s`, %s from `%s`' % (primary_key, ', '.join(escaped_fields), tablename)
        attrs[__insert__] = 'insert into `%s` (%s, `%s`) values (%s)' % (tablename, ', '.join(escaped_fields), primary_key, create_args_str(len(escaped_fields) + 1))
        attrs[__update__] = 'update `%s` set %s where `%s`=?' % (tablename, ', '.join(map(lambda f: '`%s`=?' % (mapping.get(f).name or f), fields)), primary_key)
        attrs[__delete__] = 'delete from `%s` where `%s`=?' % (tablename, primary_key)
        
        return type.__new__(cls, name, base, attrs)

class Model(dict, metaclass = ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' has no attribute '%s'" % key)
    
    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is not None:
            field = self.__mappings__[key]
            if field.default:
                value = field.default() if callable(field.default) else field.default
                logging.debug('Using default value for %s: %s' % (key, value))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where = None, args = None, **kw):
        sql = [cls.__select__]

        if where is not None:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderby = kw.get('orderBy', None)
        if orderby:
            sql.append('order by')
            sql.append(orderby)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalide limit value: %s' % str(limit))

        rs = await select_wrap(' '.join(sql), args)
        return [cls[**r] for r in rs]

    @classmethod
    async def findNumber(cls, selFields, where = None, args = None):
        sql = ['select %s _num_ from %s' % (selFields, cls.__table__)]

        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls, pk):
        rs = await select('%s where `%s`=?' % (cls.__select__, cls._primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getVauleOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if len(rows) != 1:
            logging.warn('Fail to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getVaule, self.__fields__))
        args.append(self.getVaule(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if len(rows) != 1:
            logging.warn('Fail to update from primary key: affected rows: %s', % rows)

    async def remove(self):
        args = [self.getVaule(self.__fields__)]
        rows = await execute(self.__delete__, args)
        if len(rows) != 1:
            logging.warn('Fail to remove from primar key: affected rows: %s', % rows)

