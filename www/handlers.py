#!/bin/usr/env python3
#-*- coding: utf-8 -*-

from coroweb import get, post
from models import User, Comment, Blog

@get('/')
async def index(request):
    users = await User.findAll()
    return {
            '__template__': 'test.html',
            'users': users
    }
