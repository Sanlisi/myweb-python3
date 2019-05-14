#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import config_default

class Dict(dict):
    '''
    usr-definded dict class,support x.y style
    '''

    def __init__(self, key = (), value = (), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(key, value):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' has no key of %s" % (key))

    def __setattr__(self, key, value):
        self[key] = value

def merge(default, override):
    myd = {} 
    for k, v in default.items():
        if k in override:
            if isinstance(v, dict):
                myd[k] = merge(v, override[k])
            else:
                myd[k] = override[k]
        else:
            myd[k] = v
    return myd

def toDict(d):
    myd = Dict()
    for k, v in d.items():
        myd[k] = toDict(v) if isinstance(v, dict) else v
    return myd

configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    raise ImportError('import config_override err') 

configs = toDict(configs)
