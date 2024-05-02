from flask import Flask
from flask_cors import CORS
from .extensions import db, login_manager
from .models import User



def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./bookings.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'bookingpage'

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