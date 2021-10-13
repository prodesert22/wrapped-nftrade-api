import os

from flask import Flask
from flask_caching import Cache
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from src.constants.path import PATH_SRC

PATH_DB = os.path.join(PATH_SRC, 'database')

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////'+os.path.join(PATH_DB, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cache.init_app(app)
db = SQLAlchemy(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})
