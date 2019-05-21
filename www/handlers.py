#!/bin/usr/env python3
#-*- coding: utf-8 -*-

import time

from coroweb import get, post
from models import User, Comment, Blog

@get('/')
async def logs(request):
    summary = 'I am test output, linke hello world...'
    blogs = [
            Blog(id='1', name='Test01', summary=summary, create_at=time.time()-120),
            Blog(id='2', name='Test02', summary=summary, create_at=time.time()-3600),
            Blog(id='3', name='Test03', summary=summary, create_at=time.time()-7201)
            ]
    return {
            '__template__': 'blogs.html',
            'blogs': blogs 
    }

@get('/api/users')
async def api_get_users(request):
    users = await User.findAll(orderBy='create_at desc')
    for u in users:
        u.password = '******'
    return dict(users=users)
