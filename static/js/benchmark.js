let performanceChart = null;

document.getElementById('runBenchmarkBtn').addEventListener('click', runBenchmark);

async function runBenchmark() {
    const message = document.getElementById('benchmarkMessage').value;
    const statusDiv = document.getElementById('benchmarkStatus');
    const resultsDiv = document.getElementById('benchmarkResults');
    const btn = document.getElementById('runBenchmarkBtn');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Running...';
    statusDiv.innerHTML = '<div class="alert alert-info">Running benchmarks across all security levels...</div>';
    
    try {
        const response = await fetch('/api/benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = '<div class="alert alert-success">Benchmark completed successfully!</div>';
            resultsDiv.style.display = 'block';
            
            displayResults(data.results);
            createPerformanceChart(data.results);
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill"></i> Run Benchmark';
    }
}

function displayResults(results) {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    
    const levels = ['toy', 'medium', 'strong'];
    const levelBadges = {
        'toy': 'secondary',
        'medium': 'warning text-dark',
        'strong': 'success'
    };
    
    levels.forEach(level => {
        const data = results[level];
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge bg-${levelBadges[level]}">${level.toUpperCase()}</span></td>
            <td>(${data.n}, ${data.q})</td>
            <td>${data.keygen_time}</td>
            <td>${data.encrypt_time}</td>
            <td>${data.decrypt_time}</td>
            <td><strong>${data.total_time}</strong></td>
            <td>${data.expansion_ratio}x</td>
            <td>${data.success ? '<span class="badge bg-success">✓</span>' : '<span class="badge bg-danger">✗</span>'}</td>
        `;
        tbody.appendChild(row);
    });
}

function createPerformanceChart(results) {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    if (performanceChart) {
        performanceChart.destroy();
    }
    
    const levels = ['toy', 'medium', 'strong'];
    const levelLabels = levels.map(l => l.toUpperCase());
    
    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: levelLabels,
            datasets: [
                {
                    label: 'Key Generation (ms)',
                    data: levels.map(l => results[l].keygen_time),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                },
                {
                    label: 'Encryption (ms)',
                    data: levels.map(l => results[l].encrypt_time),
                    backgroundColor: 'rgba(255, 159, 64, 0.6)',
                    borderColor: 'rgb(255, 159, 64)',
                    borderWidth: 1
                },
                {
                    label: 'Decryption (ms)',
                    data: levels.map(l => results[l].decrypt_time),
                    backgroundColor: 'rgba(153, 102, 255, 0.6)',
                    borderColor: 'rgb(153, 102, 255)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'LWE Performance by Security Level',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Time (milliseconds)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Security Level'
                    }
                }
            }
        }
    });
}
