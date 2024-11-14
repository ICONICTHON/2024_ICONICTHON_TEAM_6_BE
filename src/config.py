import os

DEBUG = True
HOST = os.environ.get('HOST','localhost')
PORT = int(os.environ.get('PORT', '5000'))
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')