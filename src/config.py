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
__C.peer.config_file = 'config.json'
