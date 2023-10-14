$(document).ready(function() {
    $('#sendButton').click(function() {
        let message = $('#userInput').val();
        $('#userInput').val('');
        $('#chatWindow').append(generateChatRow('User', message, 'icon_user.png'));
        $.ajax({
            type: 'POST',
            url: '/api/chat',
            data: JSON.stringify({ message: message }),
            contentType: 'application/json;charset=UTF-8',
            dataType: 'json',
            success: function(data) {
                $('#chatWindow').append(generateChatRow('Bot', data.response, 'icon_bot.png'));
            }
        });
    });
});

function generateChatRow(sender, message, iconSrc) {
    let chatRow = '<div class="chat-row ' + sender.toLowerCase() + '">' +
                    '<img src="' + iconSrc + '" alt="' + sender + ' Icon" class="chat-icon">' +
                    '<div class="chat-message">' +
                        '<p>' + message + '</p>' +
                    '</div>' +
                  '</div>';
    return chatRow;
}
