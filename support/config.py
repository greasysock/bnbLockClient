import os, json

default_config = 'conf.json'

def exists(file):
    return os.path.isfile(file)

def load_conf(file):
    data = {}
    with open(file) as data_file:
        data = json.load(data_file)
    return data

if exists(default_config):
    conf = load_conf(default_config)
else:
    conf = None