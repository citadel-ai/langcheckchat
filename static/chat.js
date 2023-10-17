$(document).ready(function() {
    $('#sendButton').click(sendMessage);

    // Trigger sendButton click event when Enter key is pressed
    $('#userInput').keypress(function(event) {
        if (event.which == 13) { // 13 is the Enter key's code
            event.preventDefault(); // Prevents default action (like form submission)
            sendMessage();
        }
    });

    // Handle the toggle for source text
    $('#chatWindow').on('click', '.show-source-btn', function() {
        console.log('Fired!!!');
        $(this).next('.source-text').toggleClass('hidden');
    });
});

function sendMessage() {
    let question = $('#userInput').val();
    $('#userInput').val('');

    // Clear the previous Q&A
    $('#chatWindow').empty();

    // Append the user's question
    $('#chatWindow').append(generateQuestionRow(question));

    $.ajax({
        type: 'POST',
        url: '/api/chat',
        data: JSON.stringify({ message: question }),
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        success: function(data) {
            // Append the bot's answer
            $('#chatWindow').append(generateAnswerRow(data.response + '<br><br>Factual consistency score: ' + data.score, data.source, data.warning));
        }
    });
}

function generateQuestionRow(question) {
    return '<div class="qa-block">' +
                '<div class="user-question"><strong>Q: </strong>' + question + '</div>';
}

function generateAnswerRow(answer, sourceText, warning) {
    let warning_text = '';
    if (warning) {
        warning_text = '<span style="color:red;">Warning: possible hallucination detected. </span><br>'
    }
    return '<div class="bot-answer">' + warning_text + '<strong>A: </strong>' + answer + '</div>' +
           '<button class="btn btn-sm btn-secondary show-source-btn">Show Source Text</button>' +
           '<div class="source-text hidden">' + sourceText + '</div></div>';
}