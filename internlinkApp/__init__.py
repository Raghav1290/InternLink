
from flask import Flask

app = Flask(__name__)

# My secrect key 
app.secret_key = 'SECRET_KEY_FOR_RAGHAV_INTERNLINK_PROJECT_iT_IS_SECURE'

# Setting up the database connection.
from internlinkApp import connect
from internlinkApp import db
db.init_db(app, connect.dbuser, connect.dbpass, connect.dbhost, connect.dbname,
           connect.dbport)

# Including all the necessary modules that are defining our Flask route-handling functions.
from internlinkApp import user
from internlinkApp import student
from internlinkApp import employer
from internlinkApp import admin