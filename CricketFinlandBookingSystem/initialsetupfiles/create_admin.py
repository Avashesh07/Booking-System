import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Setup Flask and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./bookings.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):

    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(64))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

def create_admin():
    with app.app_context():
        username = 'admin'
        password = 'cricketfinland23'  # Use a strong, unique password for production
        role = 'admin'

        existing_admin = User.query.filter_by(username=username).first()
        if not existing_admin:
            admin_user = User(username=username, role=role)
            admin_user.set_password(password)
            db.create_all()  # Ensure all tables are created
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created successfully.')
        else:
            print('Admin user already exists.')

if __name__ == '__main__':
    create_admin()
