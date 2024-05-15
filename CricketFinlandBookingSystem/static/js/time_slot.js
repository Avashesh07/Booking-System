let timeRanges = [];

// Populate the start and end time select elements
function populateTimeOptions() {
    const startTimeSelect = document.getElementById('startTime');
    const endTimeSelect = document.getElementById('endTime');
    const times = [];

    // Create options for every hour and half-hour from 00:00 to 23:30
    for (let hour = 9; hour < 22; hour++) {
        for (let min = 0; min < 60; min += 30) { // Increment by 30 minutes
            let timeValue = hour.toString().padStart(2, '0') + ':' + min.toString().padStart(2, '0');
            times.push(timeValue);
        }
    }

    // Append options to the selects
    times.forEach(time => {
        startTimeSelect.options.add(new Option(time, time));
        endTimeSelect.options.add(new Option(time, time));
    });
}

// Call this function to populate the selects when the script loads
populateTimeOptions();


document.getElementById('timeSlotConfigForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const increment = document.getElementById('increment').value;
    const dateRangeStart = document.getElementById('dateRangeStart').value;
    const dateRangeEnd = document.getElementById('dateRangeEnd').value;

    // Construct the time range object
    const timeRange = {
        startTime,
        endTime,
        increment,
        dateRangeStart,
        dateRangeEnd
    };

    // Send the time range object to the server
    fetch('https://booking-system-smoky.vercel.app/add_time_slot_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(timeRange)
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Time range added successfully.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save configuration.');
        });
});