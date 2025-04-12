function formatAnalysis(analysis) {
    const lines = analysis.split('\n');
    let formatted = '<h3>Analysis Summary</h3><ul>';
    lines.forEach(line => {
        if (line.trim()) {
            formatted += `<li>${line}</li>`;
        }
    });
    formatted += '</ul>';
    return formatted;
}

function formatData(data) {
    let formatted = '<h3>Data Points</h3><table><tr><th>Year</th><th>Value</th></tr>';
    data.forEach(point => {
        formatted += `<tr><td>${point.year}</td><td>${point.value.toLocaleString()}</td></tr>`;
    });
    formatted += '</table>';
    return formatted;
}

document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const query = document.getElementById('query').value;
    console.log('Submitting query:', query);
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    const result = await response.json();
    console.log('Received result:', result);
    
    // Format and display analysis
    const analysisHtml = formatAnalysis(result.analyses.merged);
    console.log('Formatted analysis:', analysisHtml);
    document.getElementById('aiAnalysis').innerHTML = analysisHtml;

    // Format and display data
    const dataHtml = formatData(result.datasets[0].data);
    console.log('Formatted data:', dataHtml);
    document.getElementById('rawData').innerHTML = dataHtml;
});