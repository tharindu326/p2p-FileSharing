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
                                    "host": "0.0.0.0",
                                    "port": 8081
                                },
                                "peers": [
                                    {
                                        "host": "0.0.0.0",
                                        "port": 8082
                                    },
                                    {
                                        "host": "0.0.0.0",
                                        "port": 8083
                                    },
                                    {
                                        "host": "0.0.0.0",
                                        "port": 8084
                                    }
                                ]
                            }

__C.network = edict()
__C.network.max_ttl = 5
