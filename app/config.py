import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Gardens grows Sox and Candles'
    REPOSITORY = 'REPOSITORY.db'
    USER_AGENT = 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'