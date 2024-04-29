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
    club_name = db.Column(db.String(128), nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Booking {self.name}, Club ID: {self.club_id}, Time: {self.time}>'

class TimeSlotConfig(db.Model):
    __tablename__ = 'time_slot_configs'  # Explicit table name definition

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(5), nullable=False)  # Stored as 'HH:MM'
    end_time = db.Column(db.String(5), nullable=False)    # Stored as 'HH:MM'
    increment = db.Column(db.Integer, nullable=False)     # Increment in minutes
    dateRangeStart = db.Column(db.Date, nullable=False)
    dateRangeEnd = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'<TimeSlotConfig {self.start_time} to {self.end_time}, every {self.increment} mins>'
