#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time;
from aiohttp import web;

def hello_index(request):
    return web.Response(body=b'<h1>Hello World!</h1>', headers={'content-type' : 'text/html'})

async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', hello_index)
    srv = await loop.create_server(app.make_handler(), '192.168.1.8', 8888)
    logging.info('server started at 192.168.1.8:8888...')
    return srv

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
