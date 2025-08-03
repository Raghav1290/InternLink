
# When our "internLinkApp" is loaded firstly then this script will run automatically and all the flask app setup will be handled by this script.


# Firstly, it will initialze the flask application then set up our session secret key 
# then establish the connection of the database and in last it will import all the modules that are defining the routes of application

from flask import Flask

app = Flask(__name__)

# Setting up the secret key which is used in signing session cookies
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