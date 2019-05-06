#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import logging, os, functools, asyncio, inspect
from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(&args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

def get_required_kw_args(fn):
    args = []
    paras = inspect.signature(fn).parameters
    for name,value in paras.items():
        if value.kind == inspect.Parameter.KEYWORD_ONLY and value.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def get_named_kw_args(fn):
    args = []
    paras = inspect.signature(fn).parameters
    for name, value in paras.items():
        if value.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

def has_named_kw_arg(fn):
    paras = inspect.signature(fn).parameters
    for name, value in paras.items():
        if value.kind == inspect.Parameter.KERYWORD_ONLY:
            return True

def has_var_kw_arg(fn):
    paras = inspect.signature(fn).parameters
    for name, value in paras.items():
        if value.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_request_arg(fn):
    paras = inspect.signature(fn).parameters
    found = 0
    for name, value in paras.items():
        if name == 'request':
            found = 1
            continue
        if found and (value.kind != inspect.Parameter.VAR_KEYWORD and value.kind != inspect.Parameter.VAR_POSITIONAL and value.kind != inspect.Parameter.KEYWORD_ONLY):
            raise ValueError('The parameter [request] must be the last named parameter in function: %s%s' % (fn.__name__, str(inspect.signature(fn))))
    return found

class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_arg = has_named_kw_arg(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_arg or self._required_kw_args:
            if request.method == 'POST':
                ct = request.content_type
                if not ct:
                    return web.HTTPBadRequest('Missing content type')
                ct = ct.lower()
                if ct.startwith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must object')
                    kw = params
                elif ct.startwith('application/x-www-form-urlencoded') or ct.startwith('mutipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return HTTPBadRequest('Unsupported Content-type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy

            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request

        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))

        try:
            r = await fun(**kw)
            return r
        except APIError as e:
            return dict(error = e.error, data = e.data, message = e.message)

def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s=>%s' % ('/static/', path))

def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if method is None or path is None:
        raise ValueError('@get or @post not define in %s' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)

    logging.info('add route %s %s=>%s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandle(app, fn))

def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1]
        mod = getattr(__import__(module_name[:n], globals(), locals()), name)
    for attr in dir(mod):
        if attr.startwith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
