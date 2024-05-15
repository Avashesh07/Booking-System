// Global variable to hold available dates
var availableDates = [];

const currentUserRole = document.body.getAttribute('data-role');

// Fetch the clubs from the server and populate the dropdown list
document.addEventListener('DOMContentLoaded', (event) => {
    fetch('https://booking-system-smoky.vercel.app/clubs')
        .then(response => response.json())
        .then(data => {
            const clubSelect = document.getElementById('club');
            data.forEach(clubName => {
                const option = document.createElement('option')
                option.value = clubName;
                option.text = clubName;
                clubSelect.appendChild(option); // Append new options below the placeholder
            });
        })
        .catch(error => console.error('Error', error));
});



$(function () {
    // Fetch the available dates from the server and store them
    fetch('https://booking-system-smoky.vercel.app/available_dates')
        .then(response => response.json())
        .then(data => {
            availableDates = data.map(date => new Date(date));
            // Refresh the datepicker after fetching available dates
            $("#datepicker").datepicker('refresh');
        })
        .catch(error => console.error('Error fetching available dates:', error));

    // Initialize the datepicker with beforeShowDay and minDate
    $("#datepicker").datepicker({
        dateFormat: "yy-mm-dd",
        minDate: new Date(), // This prevents past dates from being selected
        beforeShowDay: function (date) {
            if (currentUserRole === 'admin') {
                return [true]; // Admins can select any date
            }
            var dateStr = jQuery.datepicker.formatDate('yy-mm-dd', date);
            var isAvailable = availableDates.some(availableDate => availableDate.toDateString() === date.toDateString());
            console.log(dateStr + ' is ' + (isAvailable ? 'available' : 'not available'));
            return [isAvailable, "", ""];
        },
        onSelect: function (dateText) {
            $('#bookingDate').val(dateText);
            fetchTimeSlots(dateText);  // Fetch slots when a new date is selected
        }
    });

    function selectTimeSlot(slot, isAdmin) {
        if (!isAdmin) {
            document.getElementById('bookingTime').value = slot;
            document.querySelectorAll('.time-slot').forEach(b => b.classList.remove('selected'));
            event.target.classList.add('selected');
        }
    }
    
    function deleteBooking(bookingId) {
        fetch(`http://127.0.0.1:5001/delete_booking`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ booking_id: bookingId })
        })
        .then(response => {
            console.log(response);
            return response.json();
        })
        .then(data => {
            console.log(data);
            alert('Booking deleted');
            fetchTimeSlots(document.getElementById('bookingDate').value); // Refresh slots after deletion
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete booking');
        });
    }

    function fetchTimeSlots(date) {
        fetch(`https://booking-system-smoky.vercel.app/available_slots?date=${date}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch time slots');
                }
                return response.json();
            })
            .then(data => {
                const slotsContainer = document.querySelector('.time-slots');
                slotsContainer.innerHTML = ''; // Clear previous slots

                const isAdmin = currentUserRole === 'admin';

                data.available_slots.forEach(slot => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.classList.add('time-slot', 'available');
                    button.textContent = slot;
                    button.onclick = function() {
                        document.getElementById('bookingTime').value = slot;
                        document.querySelectorAll('.time-slot').forEach(b => b.classList.remove('selected'));
                        this.classList.add('selected');
                    };
                    slotsContainer.appendChild(button);
                });

                if (isAdmin) {
                    data.booked_slots.forEach(slot => {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.classList.add('time-slot', isAdmin ? 'admin-booked' : 'booked');
                        button.textContent = `${slot.time} - Booked by ${slot.booked_by}`;
                        button.onclick = function() {
                            if (isAdmin) {
                                deleteBooking(slot.booking_id);
                            }
                        };
                        slotsContainer.appendChild(button);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                slotsContainer.innerHTML = '<p>Error fetching time slots.</p>'; // Show error message
            });
    }
    // Set the initial value of the hidden date input to today's date
    var today = new Date();
    var dateStr = $.datepicker.formatDate('yy-mm-dd', today);
    $('#bookingDate').val(dateStr);
    fetchTimeSlots(dateStr);  // Also fetch slots right after initializing the datepicker
});



// Select the container that holds the time slots
const timeSlotsContainer = document.querySelector('.time-slots');

// Add event listener to the time slots container
timeSlotsContainer.addEventListener('click', (event) => {
    // Check if a time slot button was clicked
    if (event.target.classList.contains('time-slot')) {
        // Remove the 'selected' class from all time slot buttons
        timeSlotsContainer.querySelectorAll('.time-slot').forEach(slot => {
            slot.classList.remove('selected');
        });

        // Add the 'selected' class to the clicked time slot button
        event.target.classList.add('selected');

        // Update the value of the hidden input with the selected time
        const selectedTime = event.target.textContent || event.target.innerText;
        document.getElementById('bookingTime').value = selectedTime;
    }
});

// Handle the form submission to make a POST request to the server


document.getElementById('bookingForm').addEventListener('submit', (event) => {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const clubId = document.getElementById('club').value;  // This now works for both roles as the ID is provided in the HTML
    // Determine the club name based on the presence of the span or dropdown
    let clubNameElement = document.getElementById('club_name');
    let clubName = clubNameElement ? clubNameElement.innerText : document.querySelector("#club option:checked").text;

    // Retrieve the date and time
    const bookingDate = document.getElementById('bookingDate').value;
    const bookingTime = document.getElementById('bookingTime').value;

    // Combine date and time
    // The 'Z' indicates that this time is in UTC
    const formattedDateTime = bookingDate + 'T' + bookingTime + ':00Z';


    // The data object now includes the formattedDateTime
    const data = { name: name, email: email, time: formattedDateTime, club: clubId, club_name: clubName };



    fetch('https://booking-system-smoky.vercel.app/book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        credentials: 'include' 
    })

        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    // Throw an error with the message from the server
                    throw new Error(errorData.error);
                });
            }
            return response.json();
        })

        .then(data => {
            console.error('Success:', data);
            alert('Booking Successful!');
            // Find the booked slot and mark it as booked
            const bookedSlot = document.querySelector('.time-slot.selected');
            if (bookedSlot) {
                bookedSlot.classList.add('booked');
                bookedSlot.classList.remove('selected');
                bookedSlot.onclick = null; // Remove the click handler
            }
        })

        .catch((error) => {
            console.error('Error:', error);
            // Display an alert with the error message
            alert('Booking failed: ' + error.message);
        });
});   