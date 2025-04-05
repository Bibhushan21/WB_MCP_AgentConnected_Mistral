document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('queryInput');
    const submitButton = document.getElementById('submitQuery');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const rawDataContainer = document.getElementById('rawData');
    const aiAnalysisContainer = document.getElementById('aiAnalysis');
    const exampleQueries = document.querySelectorAll('.examples li');

    // Add click handlers for example queries
    exampleQueries.forEach(example => {
        example.addEventListener('click', () => {
            queryInput.value = example.textContent.replace(/["]/g, '');
            submitButton.click();
        });
    });

    // Handle form submission
    submitButton.addEventListener('click', async () => {
        const query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a query');
            return;
        }

        // Show loading indicator
        loadingIndicator.style.display = 'flex';
        resultContainer.style.display = 'none';
        
        try {
            // Send query to backend
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Display results
            rawDataContainer.textContent = data.raw_data;
            aiAnalysisContainer.innerHTML = formatAnalysis(data.analysis);
            
            // Hide loading, show results
            loadingIndicator.style.display = 'none';
            resultContainer.style.display = 'grid';
            resultContainer.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing your request. Please try again.');
            loadingIndicator.style.display = 'none';
        }
    });

    // Handle Enter key in input
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            submitButton.click();
        }
    });

    // Format analysis text with proper spacing and styling
    function formatAnalysis(text) {
        return text
            .split('\n')
            .map(line => {
                // Add special styling for headers
                if (line.match(/^[0-9]+\./)) {
                    return `<h3 class="analysis-header">${line}</h3>`;
                }
                // Add paragraph tags for regular text
                return line ? `<p>${line}</p>` : '';
            })
            .join('');
    }
}); 