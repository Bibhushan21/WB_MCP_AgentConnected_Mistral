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

let currentChart = null;

async function renderVisualization(mergedData, chartType = 'line') {
    // Show loading spinner
    document.getElementById('graphSpinner').style.display = 'block';

    const response = await fetch('/mcp/visualize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ merged_data: mergedData })
    });
    const visualData = await response.json();

    // Hide loading spinner
    document.getElementById('graphSpinner').style.display = 'none';

    const ctx = document.getElementById('visualizationChart').getContext('2d');

    // Destroy the existing chart if it exists
    if (currentChart) {
        currentChart.destroy();
    }

    // Create a new chart
    currentChart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: visualData.years,
            datasets: [{
                label: 'Value',
                data: visualData.values,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });
}

// Add event listener for graph type button clicks
const graphTypeButtons = document.getElementById('graphTypeButtons');
graphTypeButtons.addEventListener('click', async function(event) {
    if (event.target.tagName === 'BUTTON') {
        const selectedType = event.target.getAttribute('data-type');
        const mergedData = JSON.parse(document.getElementById('rawData').dataset.mergedData);
        await renderVisualization(mergedData, selectedType);
    }
});

async function fetchDataAndUpdateUI(query) {
    // Show loading indicators
    document.getElementById('rawDataSpinner').style.display = 'block';
    document.getElementById('aiAnalysisSpinner').style.display = 'block';
    document.getElementById('graphSpinner').style.display = 'block';

    const response = await fetch('/mcp/fetch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let result = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });

        // Process each chunk of data as it arrives
        try {
            const parsedResult = JSON.parse(result);
            updateUIWithNewData(parsedResult);
        } catch (e) {
            // Handle JSON parse errors
            console.error('Error parsing JSON:', e);
        }
    }

    // Hide loading indicators
    document.getElementById('rawDataSpinner').style.display = 'none';
    document.getElementById('aiAnalysisSpinner').style.display = 'none';
}

function updateUIWithNewData(data) {
    // Format and display analysis
    const analysisHtml = formatAnalysis(data.analyses.merged);
    document.getElementById('aiAnalysis').innerHTML = analysisHtml;

    // Format and display data
    const dataHtml = formatData(data.datasets[0].data);
    document.getElementById('rawData').innerHTML = dataHtml;
    document.getElementById('rawData').dataset.mergedData = JSON.stringify(data.datasets[0]);

    // Render visualization
    renderVisualization(data.datasets[0], 'line'); // Default to line chart initially
}

// Update the form submission to use the new fetch function
const queryForm = document.getElementById('query-form');
queryForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    const query = document.getElementById('query').value;
    console.log('Submitting query:', query);
    await fetchDataAndUpdateUI(query);
});