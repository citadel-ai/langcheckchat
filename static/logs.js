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
            // Construct the rows of the metrics table. `log` has a field
            // `metrics` which is a JSON object with the metric names as keys
            // and their values as
            // {'metric_value': value, 'explanation': explanation}. We iterate
            // over this object and construct the rows of the table.
            const metricRows = Object.entries(log.metrics).map(([metricName, metricData]) => {
              if (metricData.explanation !== null) {
                return `<tr>
                          <td id=${metricName}>${metricName}<span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${metricData.explanation.replace(/"/g, "'")}"></td>
                          <td>${round(metricData.metric_value, 4)}</td>
                        </tr>`;
              } else {
                return `<tr><td>${metricName}</td><td>${round(metricData.metric_value, 4)}</td></tr>`;
              }
            });
            const metricsTable = `<table class="table table-bordered table-hover" id="metrics-table">
                                    <thead class="thead-light">
                                      <tr>
                                        <th>Metric</th>
                                        <th>Value</th>
                                      </tr>
                                    </thead>
                                    <tbody class="text-monospace">
                                      ${metricRows.join('')}
                                    </tbody>
                                  </table>`;

            $('#qa-table').append(
                `<tr>
                    <td>${log.request}</td>
                    <td>${log.response}</td>
                    <td>${log.reference == null ? '' : log.reference}</td>
                    <td>
                        ${metricsTable}
                    </td>
                    <td>
                        <div class="d-flex justify-content-between">
                            <span class="input-preview">${log.source.substring(0, 300)}...</span>
                            <a href="#" class="show-source ml-2">Show <span data-feather="maximize-2"></span></a>
                        </div>
                        <div style="display: none; white-space: pre-wrap;">${log.source}</div>
                    </td>
                </tr>`
            );
        });
        $('#pageIndicator').text(currentPage);
        feather.replace();
        $('[data-toggle="tooltip"]').tooltip();
    }, 'json');
}

$(document).ready(function() {
    loadLogs(); // Load initial logs on page load
    $('#prevButton').click(function() { loadLogs('prev'); });
    $('#nextButton').click(function() { loadLogs('next'); });
});

$('body').on('click', '.show-source', showSource);
function showSource(e) {
  var link = $(e.currentTarget);
  var input_preview = link.prev();
  var source = link.parent().next();

  if (link.text() === 'Show ') {
    input_preview.css('visibility', 'hidden');
    input_preview.css('height', '0px');
    source.show();
    link.html('Hide ' + feather.icons['minimize-2'].toSvg());
  } else {
    input_preview.css('visibility', 'visible');
    source.hide();
    link.html('Show ' + feather.icons['maximize-2'].toSvg());
  }
  e.preventDefault();
}