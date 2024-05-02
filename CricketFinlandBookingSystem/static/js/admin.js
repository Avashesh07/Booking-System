function submitForm(event) {
    event.preventDefault();
    const clubName = document.getElementById('name').value;
    fetch('http://127.0.0.1:5001/admin/add_club', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: clubName })
    })
        .then(response => response.json())
        .then(data => alert(JSON.stringify(data)))
        .catch(error => console.error('Error:', error));
}