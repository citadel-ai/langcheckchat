$(document).ready(function() {
    $('#sendButton').click(function() {
        let message = $('#userInput').val();
        $('#userInput').val('');
        $.ajax({
            type: 'POST',
            url: '/api/chat',
            data: JSON.stringify({ message: message }),
            contentType: 'application/json;charset=UTF-8',
            dataType: 'json',
            success: function(data) {
                $('#chatWindow').append('\n' + data.response);
            }
        });
    });
});