from .extensions import db, login_manager, mail
from datetime import datetime,timedelta
from flask import request, jsonify, redirect, url_for, render_template, flash, make_response, session
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from flask_mail import Message
from werkzeug.security import generate_password_hash
from .models import Club, Booking, TimeSlotConfig, User


def set_password(self, password):
    self.password_hash = generate_password_hash(password)



def init_routes(app):

    # Initialize Flask-Login
    login_manager.init_app(app)

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
        error_message = ''  # Initialize error_message to ensure it has a value
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
                error_message = 'Invalid username or password'
                return render_template('login.html', error=error_message)

        return render_template('login.html')
    
    @app.route('/register', methods=['POST','GET'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            role = request.form['role']
            existing_user = User.query.filter_by(username=username).first()
            
            if not existing_user:
                user = User(username=username, email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                
                if role == 'club':
                    # Also register this username as a new club in the Club table
                    new_club = Club(name=username)
                    db.session.add(new_club)

                elif role == 'national_team':
                    new_club = Club(name='National Team')
                    db.session.add(new_club)
                
                db.session.commit()
                # Prepare and send the email
                try:
                    msg = Message("Registration Successful",
                                sender=app.config['MAIL_DEFAULT_SENDER'],
                                recipients=[email])
                    msg.body = f'Hi {username}, you have been successfully registered.  Your password is "{password}" and your username is "{username}". Please use the provided credentials to login.'
                    mail.send(msg)
                    response = jsonify({'message': f'Registration successful. Login details sent to {email}.'})
                    print(response.data)  # This will log the response data
                    return response, 201
                except Exception as e:
                    db.session.rollback()  # Rollback the transaction if email sending fails
                    return jsonify({'error': str(e)}), 500
            else:
                return render_template('register.html')

    @app.route('/register_page')
    @login_required
    def register_page():
        # Redirect to login if not authenticated, otherwise book_form
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('login'))
        return render_template('register.html')
            
    @app.route('/book_form')
    @login_required
    def book_form():
        club_id = None
        club_name = None

        if current_user.is_authenticated:
            if current_user.role == 'club' or current_user.role == 'national_team':
                if current_user.role == 'national_team':
                    # Assuming 'National Team' is the name in the database
                    club = Club.query.filter_by(name="National Team").first()
                else:
                    # For regular clubs, you might use the username or another attribute
                    club = Club.query.filter_by(name=current_user.username).first()
                
                if club:
                    club_id = club.id
                    club_name = club.name

        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return render_template('book_form.html', club_id=club_id, club_name=club_name)

    @app.route('/book', methods=['POST'])
    def book():
        print(current_user.is_authenticated)
        booking_data = request.json

        # Converting the time from string to a datetime object.
        # Make sure the time format in the request matches '2024-05-01T10:00:00Z'.
        booking_time = datetime.strptime(booking_data['time'], '%Y-%m-%dT%H:%M:%SZ')

        # If the booking is from a club user and uses names instead of IDs
        club = Club.query.filter_by(name=booking_data['club_name']).first() if 'club_name' in booking_data else Club.query.get(booking_data['club'])

        if not club:
            return jsonify({'error': 'Club not found'}), 404

        # HERE, ADD any validation needed, like checking if the user already has 3 bookings, etc.

        # Constraint: Check for overlapping bookings
        overlapping_bookings = Booking.query.filter(
            Booking.time == booking_time
        ).count()
        if overlapping_bookings > 0:
            return jsonify({'error': 'This time slot is already booked'}), 400

        if current_user.is_authenticated:
            if current_user.role == 'club':
                # Constraint: Booking not more than 2 weeks in advance
                if booking_time > datetime.now() + timedelta(weeks=2):
                    return jsonify({'error': 'Booking cannot be more than two weeks in advance'}), 400

                # Constraint: No more than 3 active bookings
                current_club_bookings = Booking.query.filter_by(club_id=club.id).count()
                if current_club_bookings >= 3:
                    return jsonify({'error': 'Maximum of 3 active bookings allowed'}), 400
            
            elif current_user.role == 'national_team':
                # Constraint: Booking not more than 4 weeks in advance
                if booking_time > datetime.now() + timedelta(weeks=4):
                    return jsonify({'error': 'Booking cannot be more than four weeks in advance'}), 400

                # Constraint: No more than 9 active bookings
                current_club_bookings = Booking.query.filter_by(club_id=club.id).count()
                if current_club_bookings >= 18:
                    return jsonify({'error': 'Maximum of 18 active bookings allowed'}), 400

        # Create a new Booking instance
        new_booking = Booking(name=booking_data['name'], email=booking_data['email'], club_id=club.id, club_name=club.name, time=booking_time)

        db.session.add(new_booking)

        if new_booking:
            try:
                db.session.commit()
                formatted_time = new_booking.time.strftime('%Y-%m-%d %H:%M:%S')
                # Send confirmation email
                msg = Message("Booking Confirmation",
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[booking_data['email']])
                msg.body = f"Dear {booking_data['name']}, your booking for {club.name} on {formatted_time} has been confirmed."
                mail.send(msg)
                return jsonify({'message': 'Booking successful', 'data': booking_data, 'formatted_time': formatted_time}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500

    @app.route('/admin_page')
    @login_required
    def admin_page():
        # Redirect to login if not authenticated, otherwise book_form
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('login'))
        return render_template('admin.html')

    @app.route('/time_slot_page')
    @login_required
    def time_slot_page():
        # Redirect to login if not authenticated, otherwise book_form
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('login'))
        return render_template('time_slot.html')

    
    @app.route('/logout')
    def logout():
        logout_user()  # Flask-Login logout
        session.clear()  # Clear Flask session
        response = make_response(redirect(url_for('login')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response



    @app.route('/clubs', methods=['GET'])
    def get_clubs():
        clubs = Club.query.all()
        return jsonify([club.name for club in clubs]), 200

   

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

        # Parse time strings to time objects
        start_time = datetime.strptime(data['startTime'], '%H:%M').time()
        end_time = datetime.strptime(data['endTime'], '%H:%M').time()

        # Check for existing configurations
        existing_configs = TimeSlotConfig.query.filter(
            TimeSlotConfig.dateRangeStart <= date_range_end,
            TimeSlotConfig.dateRangeEnd >= date_range_start
        ).all()

        # Identify overlapping time slots
        existing_slots = set()
        for config in existing_configs:
            current_date = config.dateRangeStart
            while current_date <= config.dateRangeEnd:
                if date_range_start <= current_date <= date_range_end:
                    current_start_time = datetime.combine(current_date, datetime.strptime(config.start_time, '%H:%M').time())
                    current_end_time = datetime.combine(current_date, datetime.strptime(config.end_time, '%H:%M').time())
                    while current_start_time < current_end_time:
                        existing_slots.add(current_start_time.time())
                        current_start_time += timedelta(minutes=config.increment)
                current_date += timedelta(days=1)

        # Add new configurations for non-overlapping time slots
        new_slots = []
        skipped_slots = []
        current_date = date_range_start
        while current_date <= date_range_end:
            current_start_time = datetime.combine(current_date, start_time)
            current_end_time = datetime.combine(current_date, end_time)
            while current_start_time < current_end_time:
                if current_start_time.time() not in existing_slots:
                    new_slots.append({
                        'date': current_date,
                        'time': current_start_time.time().strftime('%H:%M')  # Convert to string
                    })
                    # Add the new slot configuration
                    new_config = TimeSlotConfig(
                        start_time=current_start_time.time().strftime('%H:%M'),
                        end_time=(current_start_time + timedelta(minutes=int(data['increment']))).time().strftime('%H:%M'),
                        increment=int(data['increment']),
                        dateRangeStart=current_date,
                        dateRangeEnd=current_date
                    )
                    db.session.add(new_config)
                else:
                    skipped_slots.append({
                        'date': current_date,
                        'time': current_start_time.time().strftime('%H:%M')  # Convert to string
                    })
                current_start_time += timedelta(minutes=int(data['increment']))
            current_date += timedelta(days=1)

        # Commit the new configurations to the database
        if new_slots:
            try:
                db.session.commit()
                # Fetch all user emails
                users = User.query.with_entities(User.email).all()
                email_list = [user.email for user in users]
                msg = Message("New Availability Added",
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=email_list)
                msg.body = "New time slots have been added, check them out on our website!"
                mail.send(msg)
                return jsonify({'message': 'Time slot configuration added successfully', 'new_slots': new_slots, 'skipped_slots': skipped_slots}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'message': 'No new time slots were added', 'skipped_slots': skipped_slots}), 200

        
    @app.route('/available_slots', methods=['GET'])
    def available_slots():
        date_requested = request.args.get('date')
        date_as_obj = datetime.strptime(date_requested, '%Y-%m-%d').date()

        # Fetch configurations and bookings for the given date
        configs = TimeSlotConfig.query.filter(
            TimeSlotConfig.dateRangeStart <= date_as_obj,
            TimeSlotConfig.dateRangeEnd >= date_as_obj
        ).all()
        bookings = Booking.query.filter(
            db.func.date(Booking.time) == date_as_obj
        ).all()

        available_slots = []
        booked_slots = []

        # Check each time slot within the configured range
        for config in configs:
            start_time = datetime.combine(date_as_obj, datetime.strptime(config.start_time, '%H:%M').time())
            end_time = datetime.combine(date_as_obj, datetime.strptime(config.end_time, '%H:%M').time())

            while start_time < end_time:
                booking = next((b for b in bookings if b.time == start_time), None)
                if booking:
                    booked_slots.append({
                        'time': start_time.strftime('%H:%M'),
                        'booking_id': booking.id,
                        'booked_by': booking.name
                    })
                else:
                    available_slots.append(start_time.strftime('%H:%M'))
                start_time += timedelta(minutes=config.increment)

        # Provide different data based on user role
        if current_user.is_authenticated and current_user.role == 'admin':
            return jsonify({'available_slots': available_slots, 'booked_slots': booked_slots})
        else:
            return jsonify({'available_slots': available_slots, 'booked_slots': []})
    

    @app.route('/delete_booking', methods=['POST'])
    @login_required
    def delete_booking():
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        booking_id = request.json.get('booking_id')
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        try:
            db.session.delete(booking)
            db.session.commit()

            # Send cancellation email
            msg = Message("Booking Cancellation",
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[booking.email])
            msg.body = f"Your booking on {booking.time.strftime('%Y-%m-%d %H:%M')} has been cancelled."
            mail.send(msg)

            return jsonify({'message': 'Booking deleted and user notified.'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
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


    @app.after_request
    def apply_caching(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
