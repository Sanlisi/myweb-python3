#!/bin/usr/env python3
#*-* coding:utf-8 *-*

import time, uuid
from orm import Model, StringField, BooleanField, TextField, FloatField

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key = True, default = next_id, ddl = 'varchar(50)')
    name = StringField(ddl = 'varchar(50)')
    password = StringField(ddl = 'varchar(50)')
    email = StringField(ddl = 'varchar(50)')
    admin = BooleanField()
    image = StringField(ddl = 'varchar(500)')
    create_at = FloatField(default = time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key = True, default = next_id, ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    name = StringField(ddl = 'varchar(50)')
    summary = StringField(ddl = 'varchar(200)')
    content = TextField()
    create_at = FloatField(default = time.time)

class Comment(Model):
    __table__ = 'comment'

    id = StringField(primary_key = True, default = next_id, ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    blog_id = StringField(ddl = 'varchar(50)')
    content = TextField()
    create_at = FloatField(default = time.time)
