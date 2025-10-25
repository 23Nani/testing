let keysGenerated = false;
let ciphertextGenerated = false;
let noiseChart = null;

document.getElementById('generateKeysBtn').addEventListener('click', generateKeys);
document.getElementById('encryptBtn').addEventListener('click', encryptMessage);
document.getElementById('decryptBtn').addEventListener('click', decryptMessage);

async function generateKeys() {
    const securityLevel = document.getElementById('securityLevel').value;
    const resultDiv = document.getElementById('keyGenResult');
    const btn = document.getElementById('generateKeysBtn');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating...';
    
    try {
        const response = await fetch('/api/generate_keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ security_level: securityLevel })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle"></i> Keys Generated Successfully!</h6>
                    <p class="mb-1"><strong>Security Level:</strong> ${data.params.security_level.toUpperCase()}</p>
                    <p class="mb-1"><strong>Parameters:</strong> n=${data.params.n}, q=${data.params.q}, σ=${data.params.sigma}</p>
                    <p class="mb-1"><strong>Ring:</strong> ${data.params.ring_size}</p>
                    <p class="mb-1"><strong>Time:</strong> ${(data.keygen_time * 1000).toFixed(2)} ms</p>
                    <p class="mb-0"><strong>Est. Security:</strong> ${data.params.estimated_security} bits</p>
                </div>
            `;
            keysGenerated = true;
            document.getElementById('encryptBtn').disabled = false;
            document.getElementById('decryptBtn').disabled = false;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-key-fill"></i> Generate Keys';
    }
}

async function encryptMessage() {
    const message = document.getElementById('plaintext').value;
    const resultDiv = document.getElementById('encryptResult');
    const btn = document.getElementById('encryptBtn');
    
    if (!message) {
        resultDiv.innerHTML = '<div class="alert alert-warning">Please enter a message</div>';
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Encrypting...';
    
    try {
        const response = await fetch('/api/encrypt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle"></i> Message Encrypted!</h6>
                    <p class="mb-1"><strong>Ciphertext Size:</strong> ${data.ciphertext.u_size + data.ciphertext.v_size} coefficients</p>
                    <p class="mb-1"><strong>Time:</strong> ${(data.encrypt_time * 1000).toFixed(2)} ms</p>
                    <div class="code-display mt-2">
                        u: [${data.ciphertext.u_sample.join(', ')}...]<br>
                        v: [${data.ciphertext.v_sample.join(', ')}...]
                    </div>
                    <div class="mt-3">
                        <label class="form-label"><strong>Hex Ciphertext (Copy to share):</strong></label>
                        <div class="input-group">
                            <textarea class="form-control" id="hexOutput" rows="3" readonly>${data.hex_ciphertext}</textarea>
                            <button class="btn btn-outline-secondary" type="button" onclick="copyHexCiphertext()">
                                <i class="bi bi-clipboard"></i> Copy
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            visualizeEncryption(data.visualization);
            ciphertextGenerated = true;
            document.getElementById('decryptBtn').disabled = false;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-lock"></i> Encrypt Message';
    }
}

async function decryptMessage() {
    const resultDiv = document.getElementById('decryptResult');
    const btn = document.getElementById('decryptBtn');
    const hexInput = document.getElementById('hexCiphertext').value.trim();
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Decrypting...';
    
    try {
        const response = await fetch('/api/decrypt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hex_ciphertext: hexInput })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-unlock-fill"></i> Message Decrypted!</h6>
                    <p class="mb-1"><strong>Time:</strong> ${(data.decrypt_time * 1000).toFixed(2)} ms</p>
                    <div class="result-box success-box mt-2">
                        <strong>Decrypted Message:</strong><br>
                        <span style="font-size: 1.2em;">${data.message}</span>
                    </div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-unlock"></i> Decrypt Message';
    }
}

function copyHexCiphertext() {
    const hexOutput = document.getElementById('hexOutput');
    hexOutput.select();
    document.execCommand('copy');
    
    // Show feedback
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check"></i> Copied!';
    setTimeout(() => {
        btn.innerHTML = originalHTML;
    }, 2000);
}

function visualizeEncryption(vizData) {
    const vizCard = document.getElementById('visualizationCard');
    vizCard.style.display = 'block';
    
    const ctx = document.getElementById('noiseChart').getContext('2d');
    
    if (noiseChart) {
        noiseChart.destroy();
    }
    
    const indices = vizData.message_poly.map((_, i) => i);
    
    noiseChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: indices,
            datasets: [
                {
                    label: 'Message Polynomial',
                    data: vizData.message_poly,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                },
                {
                    label: 'Error e1 (Noise)',
                    data: vizData.errors.e1,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                },
                {
                    label: 'Error e2 (Noise)',
                    data: vizData.errors.e2,
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Encryption Components: Message + Noise = Security'
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
                        text: 'Coefficient Value'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Polynomial Coefficient Index'
                    }
                }
            }
        }
    });
}
