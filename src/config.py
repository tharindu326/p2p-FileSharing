#! /usr/bin/env python
# coding=utf-8
from easydict import EasyDict as edict

__C = edict()
cfg = __C

__C.file = edict()
__C.file.chunk_size = 4096
__C.file.shared_directory = '../shared/'
__C.file.save_directory = '../downloads/'

__C.peer = edict()
__C.peer.configuration = {
                                "self": {
                                    "host": "127.0.0.1",
                                    "port": 8081
                                },
                                "peers": [
                                    {
                                        "host": "127.0.0.1",
                                        "port": 8082
                                    },
                                    {
                                        "host": "127.0.0.1",
                                        "port": 8083
                                    }
                                ]
                            }
