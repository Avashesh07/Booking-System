function handleSubmit(event) {
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/register',
        data: $('#registerForm').serialize(),
        success: function(response) {
            $('#modalMessage').text(response.message);
            $('#registerModal').modal('show');
        },
        error: function(response) {
            $('#modalMessage').text(response.responseJSON.error);
            $('#registerModal').modal('show');
        }
    });
}