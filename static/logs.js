let currentPage = 1;

function loadLogs(direction) {
    if (direction === 'next') {
        currentPage += 1;
    } else if (direction === 'prev' && currentPage > 1) {
        currentPage -= 1;
    }
    $('#qa-table tr:not(:first)').remove();  // Remove all rows except headers
    $.get('/api/logs?page=' + currentPage, function(data) {
        data.logs.forEach(log => {
            $('#qa-table').append(
                '<tr><td>' + log.request + '</td><td>' + log.response + '</td><td>' + log.timestamp + '</td></tr>'
            );
        });
        $('#pageIndicator').text(currentPage);
    }, 'json');
}

$(document).ready(function() {
    loadLogs(); // Load initial logs on page load
    $('#prevButton').click(function() { loadLogs('prev'); });
    $('#nextButton').click(function() { loadLogs('next'); });
});
