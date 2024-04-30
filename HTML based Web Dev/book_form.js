// Global variable to hold available dates
var availableDates = [];

// Fetch the clubs from the server and populate the dropdown list
document.addEventListener('DOMContentLoaded', (event) => {
    fetch('http://127.0.0.1:5001/clubs')
        .then(response => response.json())
        .then(data => {
            const clubSelect = document.getElementById('club');
            data.forEach(clubName => {
                const option = document.createElement('option')
                option.value = clubName;
                option.text = clubName;
                clubSelect.add(option);
            });
        })
        .catch(error => console.error('Error', error));
});

$(function () {
    // Fetch the available dates from the server and store them
    fetch('http://localhost:5001/available_dates')
        .then(response => response.json())
        .then(data => {
            // Update the availableDates array
            availableDates = data.map(date => new Date(date));
            // Now that we have the available dates, refresh the datepicker
            $("#datepicker").datepicker('refresh');  // This line refreshes the datepicker
        })
        .catch(error => console.error('Error fetching available dates:', error));

    // Initialize the datepicker with beforeShowDay function
    $("#datepicker").datepicker({
        dateFormat: "yy-mm-dd",
        beforeShowDay: function (date) {
            var dateStr = jQuery.datepicker.formatDate('yy-mm-dd', date);
            var isAvailable = availableDates.some(function (availableDate) {
                return availableDate.toDateString() === date.toDateString();
            });
            console.log(dateStr + ' is ' + (isAvailable ? 'available' : 'not available'));
            return [isAvailable, "", ""];
        },
        onSelect: function (dateText) {
            $('#bookingDate').val(dateText);
            fetchTimeSlots(dateText);  // Fetch slots when a new date is selected
        }
    });

    function fetchTimeSlots(date) {
        fetch(`http://localhost:5001/available_slots?date=${date}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('No time slots available for the selected date');
                }
                return response.json();
            })
            .then(slots => {
                // Sort the slots by time before creating buttons
                slots.sort((a, b) => {
                    // Convert time slots to date objects to compare
                    const timeA = new Date(`1970-01-01T${a}:00Z`);
                    const timeB = new Date(`1970-01-01T${b}:00Z`);
                    return timeA - timeB;
                });

                const slotsContainer = document.querySelector('.time-slots');
                slotsContainer.innerHTML = ''; // Clear previous slots

                // Create a button for each slot
                slots.forEach(slot => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.classList.add('time-slot');
                    button.textContent = slot;
                    button.onclick = function () {
                        document.getElementById('bookingTime').value = date + 'T' + slot + ':00Z';
                        // Deselect other buttons and select this one
                        document.querySelectorAll('.time-slot').forEach(b => b.classList.remove('selected'));
                        button.classList.add('selected');
                    };
                    slotsContainer.appendChild(button);
                });
            })
            .catch(error => {
                console.error(error);
                const slotsContainer = document.querySelector('.time-slots');
                slotsContainer.innerHTML = '<p>No available time slots for this date.</p>'; // Show message
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
    const club = document.getElementById('club');
    const clubId = club.options[club.selectedIndex].value;
    const clubName = club.options[club.selectedIndex].text;

    // Retrieve the date and time
    const bookingDate = document.getElementById('bookingDate').value;
    const bookingTime = document.getElementById('bookingTime').value;

    // Combine date and time
    // The 'Z' indicates that this time is in UTC
    const formattedDateTime = bookingDate + 'T' + bookingTime + ':00Z';


    // The data object now includes the formattedDateTime
    const data = { name: name, email: email, time: formattedDateTime, club: clubId, club_name: clubName };



    fetch('http://localhost:5001/book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
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