from .extensions import db, login_manager
from datetime import datetime,timedelta
from flask import request, jsonify, redirect, url_for, render_template, flash
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash
from .models import Club, Booking, TimeSlotConfig, User

def init_routes(app):


    # Initialize Flask-Login
    login_manager = LoginManager()

    # User Loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def home():
        # Redirect to login if not authenticated, otherwise book_form
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return redirect(url_for('book_form'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('book_form'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('book_form'))
            else:
                flash('Invalid username or password')
        return render_template('login.html')

    @app.route('/book_form')
    @login_required
    def book_form():
        return render_template('book_form.html')

    @app.route('/admin_page')
    @login_required
    def admin_page():
        if current_user.role != 'admin':
            flash("You do not have permission to view this page.")
            return redirect(url_for('book_form'))
        return render_template('admin.html')

    @app.route('/time_slot_page')
    @login_required
    def time_slot_page():
        if current_user.role != 'admin':
            flash("You do not have permission to view this page.")
            return redirect(url_for('book_form'))
        return render_template('time_slot.html')

    @app.route('/signup_page')
    @login_required
    def signup_page():
        if current_user.role != 'admin':
            flash("You do not have permission to view this page.")
            return redirect(url_for('book_form'))
        return render_template('signup.html')
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))

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
        new_booking = Booking(name=booking_data['name'], club_id=club.id, club_name=club.name, time=booking_time)

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


    @app.route('/add_time_slot_config', methods=['POST'])
    def add_time_slot_config():
        data = request.get_json()

        # Parse date strings to date objects
        date_format = "%Y-%m-%d"
        try:
            date_range_start = datetime.strptime(data['dateRangeStart'], date_format).date()
            date_range_end = datetime.strptime(data['dateRangeEnd'], date_format).date()
        except ValueError as e:
            # Handle incorrect date format
            return jsonify({'error': str(e)}), 400

        # Check if the range for the given date already exists
        existing_config = TimeSlotConfig.query.filter(
            TimeSlotConfig.dateRangeStart <= date_range_end,
            TimeSlotConfig.dateRangeEnd >= date_range_start
        ).first()

        if existing_config:
            return jsonify({'error': 'Range already exists for the given dates'}), 400

        # Proceed to add the new configuration if it doesn't exist
        new_config = TimeSlotConfig(
            start_time=data['startTime'],
            end_time=data['endTime'],
            increment=int(data['increment']),
            dateRangeStart=date_range_start,
            dateRangeEnd=date_range_end
        )
        db.session.add(new_config)
        db.session.commit()
        return jsonify({'message': 'Time slot configuration added successfully'}), 201


    @app.route('/available_slots', methods=['GET'])
    def available_slots():
        date_requested = request.args.get('date')
        date_as_obj = datetime.strptime(date_requested, '%Y-%m-%d').date()
        
        configs = TimeSlotConfig.query.filter(
            TimeSlotConfig.dateRangeStart <= date_as_obj,
            TimeSlotConfig.dateRangeEnd >= date_as_obj
        ).all()
        
        if not configs:
            return jsonify({'error': 'No time slots available for the selected date'}), 404
        
        available_slots = []
        # Assuming configs contains non-overlapping time ranges
        for config in configs:
            start_time = datetime.combine(date_as_obj, datetime.strptime(config.start_time, '%H:%M').time())
            end_time = datetime.combine(date_as_obj, datetime.strptime(config.end_time, '%H:%M').time())
            
            while start_time < end_time:
                if not Booking.query.filter_by(time=start_time).first():
                    available_slots.append(start_time.strftime('%H:%M'))
                start_time += timedelta(minutes=config.increment)
        
        return jsonify(available_slots)

    @app.route('/available_dates', methods=['GET'])
    def available_dates():
        # Get all the configurations for time slots
        configs = TimeSlotConfig.query.all()
        # Prepare a list to hold available dates
        available_dates_list = []
        
        # Loop through each configuration
        for config in configs:
            current_date = config.dateRangeStart
            while current_date <= config.dateRangeEnd:
                # Check each time slot for the current date to see if it's available
                start_time = datetime.combine(current_date, datetime.strptime(config.start_time, '%H:%M').time())
                end_time = datetime.combine(current_date, datetime.strptime(config.end_time, '%H:%M').time())
                time_slot_available = False
                
                while start_time < end_time:
                    # Check if a booking already exists for the given time slot
                    if not Booking.query.filter_by(time=start_time).first():
                        time_slot_available = True
                        break
                    # Increment the time slot
                    start_time += timedelta(minutes=config.increment)
                
                # If at least one time slot is available, add the date to the list
                if time_slot_available:
                    available_dates_list.append(current_date.strftime('%Y-%m-%d'))
                
                # Go to the next date
                current_date += timedelta(days=1)
        
        # Remove duplicates before returning the list
        unique_dates = list(set(available_dates_list))
        return jsonify(unique_dates)
    

    
    @app.route('/cleanup', methods=['GET'])

    def cleanup_old_bookings():
        # Get current date and time
        current_time = datetime.now()
        # Delete bookings that have passed
        deleted_count = Booking.query.filter(Booking.time < current_time).delete()
        db.session.commit()
        return jsonify({'message': f'Cleaned up {deleted_count} old bookings'}), 200

