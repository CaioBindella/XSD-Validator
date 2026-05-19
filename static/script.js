async function uploadAndProcess() {
    const fileInput = document.getElementById('xmlFile');
    const file = fileInput.files[0];
    const spinner = document.getElementById('loadingSpinner');

    if (!file) {
        alert("Please select a file first.");
        return;
    }

    // Reset da Interface
    spinner.style.display = 'inline-block';
    document.getElementById('list-success').innerHTML = '';
    document.getElementById('list-warning').innerHTML = '';
    document.getElementById('list-error').innerHTML = '';
    document.getElementById('invalid-downloads-container').style.display = 'none';
    document.getElementById('warning-downloads-container').style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            alert("Error: " + data.error);
            return;
        }

        updateInterface(data);

    } catch (error) {
        console.error('Network Error:', error);
        alert("A network error occurred while connecting to the server.");
    } finally {
        spinner.style.display = 'none';
    }
}

function updateInterface(data) {
    // Atualiza os contadores das abas
    document.getElementById('count-success').innerText = data.success.length;
    document.getElementById('count-error').innerText = data.errors.length;

    // Popula a Aba de Sucesso e a Aba de Warnings
    const tbodySuccess = document.getElementById('list-success');
    const tbodyWarning = document.getElementById('list-warning');
    const warningDownloadsContainer = document.getElementById('warning-downloads-container');
    const csvWarningBtn = document.getElementById('csv-warning-download-btn');
    
    let warningCount = 0;

    if (data.success.length === 0) {
        tbodySuccess.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-4">No valid trials found.</td></tr>';
        tbodyWarning.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-4">No warnings found.</td></tr>';
    } else {
        let htmlSuccess = '';
        let htmlWarning = '';
        
        data.success.forEach(item => {
            if (item.warnings && item.warnings.length > 0) {
                // Monta o visual para a aba de Success (como já estava)
                let warningsList = item.warnings.map(w => `<li>${w}</li>`).join('');
                htmlSuccess += `<tr class="table-warning">
                    <td class="align-middle"><strong>${item.id}</strong></td>
                    <td>
                        ${item.file}
                        <div class="mt-2 text-dark">
                            <strong><i class="bi bi-exclamation-triangle-fill text-warning"></i> Warning - Truncated Fields:</strong>
                            <ul class="mb-0" style="font-size: 0.85em; color: #856404;">
                                ${warningsList}
                            </ul>
                        </div>
                    </td>
                    <td class="align-middle"><span class="badge bg-success text-dark">Valid (Truncated)</span></td>
                </tr>`;
                
                // --- NOVO: Monta o visual exclusivo para a nova aba Warnings ---
                warningCount += 1;
                htmlWarning += `<tr>
                    <td class="align-middle fw-bold text-dark">${item.id}</td>
                    <td class="align-middle">${item.file}</td>
                    <td>
                        <ul class="mb-0" style="font-size: 0.85em; color: #856404;">
                            ${warningsList}
                        </ul>
                    </td>
                </tr>`;
                
            } else {
                htmlSuccess += `<tr>
                    <td class="align-middle fw-bold text-dark">${item.id}</td>
                    <td class="align-middle">${item.file}</td>
                    <td class="align-middle"><span class="badge bg-success">Valid</span></td>
                </tr>`;
            }
        });
        
        tbodySuccess.innerHTML = htmlSuccess;
        
        // Atualiza a aba de Warning
        document.getElementById('count-warning').innerText = warningCount;
        
        if (warningCount === 0) {
            tbodyWarning.innerHTML = '<tr><td colspan="3" class="text-center text-success py-4"><i class="bi bi-check-circle-fill fs-4 d-block mb-2"></i> Great! No warnings found.</td></tr>';
        } else {
            tbodyWarning.innerHTML = htmlWarning;
            
            // Ativa o botão de download de CSV de Warning
            if (data.csv_warning_report && warningDownloadsContainer) {
                csvWarningBtn.href = '/download/' + data.csv_warning_report;
                warningDownloadsContainer.style.display = 'block';
            }
        }
    }

    // Popula a Aba de Erros (Invalid)
    const divError = document.getElementById('list-error');
    const invalidDownloadsContainer = document.getElementById('invalid-downloads-container');
    const csvBtn = document.getElementById('csv-download-btn');

    if (data.errors.length === 0) {
        divError.innerHTML = '<p class="text-center text-success py-4"><i class="bi bi-check-circle-fill fs-4 d-block mb-2"></i> Great! No validation errors found.</p>';
        if (invalidDownloadsContainer) invalidDownloadsContainer.style.display = 'none';
    } else {
        if (data.csv_report && invalidDownloadsContainer) {
            csvBtn.href = '/download/' + data.csv_report;
            invalidDownloadsContainer.style.display = 'block';
        }

        let html = '';
        data.errors.forEach(item => {
            let reasonsList = item.reasons.map(r => `<li>${r}</li>`).join('');
            html += `
            <div class="card mb-3 border-danger shadow-sm">
                <div class="card-header bg-danger text-white d-flex justify-content-between align-items-center py-2">
                    <span>Trial ID: <strong>${item.id}</strong></span>
                    <span style="font-size: 0.85em; opacity: 0.9;"><i class="bi bi-folder2-open"></i> ${item.folder}</span>
                </div>
                <div class="card-body bg-light">
                    <h6 class="card-title text-danger fw-bold"><i class="bi bi-exclamation-octagon-fill"></i> Validation Errors:</h6>
                    <ul class="error-log mb-0 ps-3">
                        ${reasonsList}
                    </ul>
                </div>
            </div>`;
        });
        divError.innerHTML = html;
    }
}