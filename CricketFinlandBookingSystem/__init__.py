from flask import Flask
from flask_cors import CORS
from .extensions import db, login_manager,mail
from .models import User
from flask_mail import Mail
import os
from dotenv import load_dotenv



def create_app():

    load_dotenv() 

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./bookings.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'bookingpage'

    # Configuration for Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'  # Use your SMTP server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') 
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')   

    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import init_routes
    init_routes(app)

    with app.app_context():
        db.create_all()

    return app