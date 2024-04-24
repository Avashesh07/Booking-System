from . import db
from datetime import datetime,timedelta
from flask import request, jsonify
from .models import Club, Booking

def init_routes(app):

    @app.route('/')
    def home():
        return jsonify({'message': 'Welcome to the Booking System API!'})


    @app.route('/admin/add_club', methods=['POST'])
    def add_club():
        if 'name' not in request.json:
            return jsonify({'error': 'Bad request, club name is required'}), 400

        club_name = request.json['name']
        existing_club = Club.query.filter_by(name=club_name).first()
        if existing_club:
            return jsonify({'error': 'Club already exists'}), 409

        new_club = Club(name=club_name)
        db.session.add(new_club)
        try:
            db.session.commit()
            return jsonify({'message': f'Club {club_name} added successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/clubs', methods=['GET'])
    def get_clubs():
        clubs = Club.query.all()
        return jsonify([club.name for club in clubs]), 200

    @app.route('/book', methods=['POST'])
    def book():
        booking_data = request.json

        # Converting the time from string to a datetime object.
        # Make sure the time format in the request matches '2024-05-01T10:00:00Z'.
        booking_time = datetime.strptime(booking_data['time'], '%Y-%m-%dT%H:%M:%SZ')

        # Fetch the club using the club name provided in the booking data
        club = Club.query.filter_by(name=booking_data['club']).first()
        if not club:
            return jsonify({'error': 'Club not found'}), 404

        # HERE, ADD any validation needed, like checking if the user already has 3 bookings, etc.

        # Constraint: Check for overlapping bookings
        overlapping_bookings = Booking.query.filter(
            Booking.time == booking_time
        ).count()
        if overlapping_bookings > 0:
            return jsonify({'error': 'This time slot is already booked'}), 400


        # Constraint: Booking not more than 2 weeks in advance
        if booking_time > datetime.now() + timedelta(weeks=2):
            return jsonify({'error': 'Booking cannot be more than two weeks in advance'}), 400

        # Constraint: No more than 3 active bookings
        current_club_bookings = Booking.query.filter_by(club_id=club.id).count()
        if current_club_bookings >= 3:
            return jsonify({'error': 'Maximum of 3 active bookings allowed'}), 400

        # Create a new Booking instance
        new_booking = Booking(name=booking_data['name'], club_id=club.id, time=booking_time)

        db.session.add(new_booking)

        try:
            db.session.commit()
            formatted_time = new_booking.time.strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'message': 'Booking successful', 'data': booking_data, 'formatted_time': formatted_time}), 201
        
        except Exception as e:
            # For production use, it's not a good idea to expose the exception message.
            # This is just for debugging.
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


    @app.route('/cleanup', methods=['GET'])

    def cleanup_old_bookings():
        # Get current date and time
        current_time = datetime.now()
        # Delete bookings that have passed
        deleted_count = Booking.query.filter(Booking.time < current_time).delete()
        db.session.commit()
        return jsonify({'message': f'Cleaned up {deleted_count} old bookings'}), 200

