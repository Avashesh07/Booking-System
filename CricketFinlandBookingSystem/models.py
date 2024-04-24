from . import db  # Assuming db is initialized in your __init__.py using SQLAlchemy

class Club(db.Model):
    __tablename__ = 'clubs'  # Explicit table name definition (optional)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Relationship to bookings
    bookings = db.relationship('Booking', backref='club', lazy=True)

    def __repr__(self):
        return f'<Club {self.name}>'

class Booking(db.Model):
    __tablename__ = 'bookings'  # Explicit table name definition (optional)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Booking {self.name}, Club ID: {self.club_id}, Time: {self.time}>'
