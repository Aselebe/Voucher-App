from flask import Flask
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from routes import create_routes  # Import your routes

# Initialize the app
app = Flask(__name__)
app.secret_key = '1234'
bcrypt = Bcrypt(app)
mail = Mail(app)

# Register the routes
create_routes(app)

# Additional configuration for mail, logging, etc.
import logging
app.logger.setLevel(logging.DEBUG)