from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./bookings.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import routes after the Flask app instance is created
    from .routes import init_routes
    # Import models to ensure they are known to SQLAlchemy
    init_routes(app)
    with app.app_context():
        db.create_all()

    return app