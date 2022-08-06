import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    AUTHOR = 'B. Watremetz'
    VERSION = 0.1
    SQLALCHEMY_TRACK_MODIFICATIONS = False