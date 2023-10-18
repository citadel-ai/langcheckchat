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
let metricsPollingInterval;

function sendMessage() {
    let question = $('#userInput').val();
    $('#userInput').val('');

    if (question.trim() === "") return;  // Don't send an empty message

    const language = $("#languageSelect").val();

    // Clear the previous Q&A
    $('#chatWindow').empty();

    // Append the user's question
    $('#chatWindow').append(generateQuestionRow(question));

    $('#metricsTable tbody').empty();

    $.ajax({
        type: 'POST',
        url: '/api/chat',
        data: JSON.stringify({ message: question, language: language }),
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        success: function(data) {
            // Append the bot's answer
            // Poll metrics every second
            if (metricsPollingInterval !== undefined) {
                clearInterval(metricsPollingInterval);
            }
            $('#metricsContainer').removeClass('hidden');
            metricsPollingInterval = setInterval(updateMetrics.bind(null, data.id), 1000);
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
    return '<div class="qa-block">' +
                '<div class="bot-answer">' + warning_text + '<strong>A: </strong>' + answer + '</div>' +
                '<button class="btn btn-sm btn-secondary show-source-btn">Show Source Text</button>' +
                '<div class="source-text hidden">' + sourceText + '</div></div>' +
            '</div>';
}

function updateMetrics(id) {
    $.ajax({
        type: 'GET',
        url: '/api/metrics/' + id,
        dataType: 'json',
        success: function(data) {
            $('#metricsTable tbody').empty();

            for (let metric in data) {
                if (metric !== "completed") {
                    let value = data[metric] !== null ? data[metric] : '<img src="static/spinner.gif" alt="Loading..." class="spinner">';
                    $('#metricsTable tbody').append(`<tr><td>${metric}</td><td>${value}</td></tr>`);
                }
            }

            if (data.completed) {
                // Stop polling if metrics computation is completed
                clearInterval(metricsPollingInterval);
            }
        }
    });
}
