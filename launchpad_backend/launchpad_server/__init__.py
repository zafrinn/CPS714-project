import os
from flask import Flask

# initalize app and setup app configs
app = Flask(__name__)

# routes has to be imported after app config and initalizaiton 
from launchpad_server.routes import index, login

