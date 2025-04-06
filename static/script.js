document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultsSection = document.querySelector('.results-section');
    const statsContainer = document.getElementById('stats');
    const previewContainer = document.getElementById('preview');
    const downloadBtn = document.getElementById('downloadBtn');
    const newFileBtn = document.getElementById('newFileBtn');
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    const tryAgainBtn = document.getElementById('tryAgainBtn');

    let currentCleanedFilename = '';

    uploadBtn.addEventListener('click', handleUpload);
    downloadBtn.addEventListener('click', () => downloadCleanedData(currentCleanedFilename));
    newFileBtn.addEventListener('click', resetForm);
    tryAgainBtn.addEventListener('click', resetForm);

    async function handleUpload(event) {
        event.preventDefault();
        const file = fileInput.files[0];
        if (!file) {
            showError('Please select a file first!');
            return;
        }

        resetForm();
        progressSection.classList.remove('hidden');
        updateProgress(10, 'Starting upload...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            updateProgress(30, 'Uploading file...');
            
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }

            updateProgress(70, 'Processing data...');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            updateProgress(90, 'Finalizing...');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            updateProgress(100, 'Cleaning complete!');
            
            // Store the cleaned filename for download
            currentCleanedFilename = data.cleaned_filename;
            
            // Show results
            showResults(data.report, data.preview);
            
        } catch (error) {
            showError(error.message);
        }
    }

    function showResults(report, previewData) {
        progressSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
        // Display statistics
        statsContainer.innerHTML = `
            <div class="stat-card">
                <h4>Original Data</h4>
                <p>Rows: ${report.original_rows}</p>
                <p>Columns: ${report.original_cols}</p>
            </div>
            <div class="stat-card">
                <h4>Cleaned Data</h4>
                <p>Rows: ${report.cleaned_rows}</p>
                <p>Columns: ${report.cleaned_cols}</p>
            </div>
            <div class="stat-card">
                <h4>Data Quality</h4>
                <p>Missing Values: ${report.missing_values}</p>
                <p>Duplicates Removed: ${report.duplicates_removed}</p>
                <p>Outliers Treated: ${report.outliers_treated}</p>
            </div>
        `;

        // Display data preview
        displayDataPreview(previewData);
    }

    async function downloadCleanedData(filename) {
        try {
            if (!filename) {
                throw new Error('No cleaned data available to download');
            }
            
            const response = await fetch(`/download/${filename}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            showError('Download failed: ' + error.message);
        }
    }

    function displayDataPreview(data) {
        if (!data || data.length === 0) {
            previewContainer.innerHTML = '<p>No preview data available</p>';
            return;
        }

        // Get all unique keys from the data
        const headers = Object.keys(data[0]);
        
        let html = '<thead><tr>';
        headers.forEach(header => {
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                html += `<td>${row[header] !== null ? row[header] : ''}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody>';
        previewContainer.innerHTML = html;
    }

    function updateProgress(percent, message) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = message;
    }

    function showError(message) {
        progressSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = message;
    }

    function resetForm() {
        fileInput.value = '';
        progressSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        progressBar.style.width = '0%';
        currentCleanedFilename = '';
    }
});