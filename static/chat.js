$(document).ready(function() {
    $('#sendButton').click(function() {
        let message = $('#userInput').val();
        $('#userInput').val('');
        $('#chatWindow').empty();
        $('#chatWindow').append(generateChatRow('User', message, 'icon_user.png'));
        $.ajax({
            type: 'POST',
            url: '/api/chat',
            data: JSON.stringify({ message: message }),
            contentType: 'application/json;charset=UTF-8',
            dataType: 'json',
            success: function(data) {
                console.log(data);
                $('#chatWindow').append(generateChatRow('Bot', data.response + '<br><br>Factual consistency score: ' + data.score, 'icon_bot.png', data.warning));
            }
        });
    });
});

function generateChatRow(sender, message, iconSrc, warning) {
    let warning_text = '';
    if (warning) {
        warning_text = '<span style="color:red;">Warning: possible hallucination detected. </span><br>'
    }
    let chatRow = '<div class="chat-row ' + sender.toLowerCase() + '">' +
                    '<img src="/static/' + iconSrc + '" alt="' + sender + ' Icon" class="chat-icon">' +
                    '<div class="chat-message">' +
                         warning_text + message +
                    '</div>' +
                  '</div>';
    return chatRow;
}
