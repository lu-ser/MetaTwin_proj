// dashboard.js - Funzioni per la dashboard

document.addEventListener('DOMContentLoaded', function () {
    // Verifica l'autenticazione all'avvio
    if (!isAuthenticated()) {
        // Mostra direttamente l'interfaccia di login nella dashboard invece di reindirizzare
        showLoginInterface();
        return;
    }

    // Carica i dati dell'utente nella navbar
    loadUserInfo();

    // Carica i digital twins
    loadDigitalTwins();

    // Gestione del parametro dt nell'URL per selezionare automaticamente un digital twin
    const urlParams = new URLSearchParams(window.location.search);
    const selectedDt = urlParams.get('dt');
    if (selectedDt) {
        loadDigitalTwinDetails(selectedDt);
    }
});

// Mostra l'interfaccia di login direttamente nella dashboard
function showLoginInterface() {
    // Nascondi i contenuti della dashboard
    const dashboardContents = document.querySelectorAll('.row');
    dashboardContents.forEach(el => {
        el.style.display = 'none';
    });

    // Crea il contenitore per il login
    const loginContainer = document.createElement('div');
    loginContainer.className = 'row mt-5';
    loginContainer.innerHTML = `
        <div class="col-md-6 offset-md-3">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">Accedi alla Dashboard</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger" id="loginError" style="display: none;"></div>
                    
                    <form id="dashboardLoginForm">
                        <div class="mb-3">
                            <label for="dashEmail" class="form-label">Email</label>
                            <input type="email" class="form-control" id="dashEmail" required>
                        </div>
                        <div class="mb-3">
                            <label for="dashPassword" class="form-label">Password</label>
                            <input type="password" class="form-control" id="dashPassword" required>
                        </div>
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-primary">Accedi</button>
                        </div>
                    </form>
                    
                    <hr>
                    <div class="text-center">
                        <p class="mb-0">Non hai un account? <a href="#" id="dashRegisterLink">Registrati</a></p>
                    </div>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0">Hai già un token?</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        Se hai già un token JWT puoi inserirlo qui per autenticarti.
                    </div>
                    <div class="mb-3">
                        <label for="manualToken" class="form-label">Token JWT</label>
                        <input type="text" class="form-control" id="manualToken" placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...">
                    </div>
                    <div class="d-grid gap-2">
                        <button id="useTokenBtn" class="btn btn-secondary">Usa Token</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Aggiungi il container alla pagina
    document.querySelector('.container').appendChild(loginContainer);

    // Event listener per il form di login
    document.getElementById('dashboardLoginForm').addEventListener('submit', function (e) {
        e.preventDefault();
        handleDashboardLogin();
    });

    // Event listener per il link di registrazione
    document.getElementById('dashRegisterLink').addEventListener('click', function (e) {
        e.preventDefault();
        window.location.href = '/api/v1/login'; // Vai alla pagina di login che ha il link per registrarsi
    });

    // Event listener per l'inserimento manuale del token
    document.getElementById('useTokenBtn').addEventListener('click', function () {
        const token = document.getElementById('manualToken').value.trim();
        if (token) {
            localStorage.setItem('auth_token', token);
            // Ricarica la pagina per verificare il token
            window.location.reload();
        } else {
            const loginError = document.getElementById('loginError');
            loginError.textContent = 'Inserisci un token valido';
            loginError.style.display = 'block';
        }
    });
}

// Gestisce il login dalla dashboard
async function handleDashboardLogin() {
    const email = document.getElementById('dashEmail').value;
    const password = document.getElementById('dashPassword').value;
    const loginError = document.getElementById('loginError');

    try {
        loginError.style.display = 'none';

        // OAuth2 richiede i dati nel formato "application/x-www-form-urlencoded"
        const formData = new URLSearchParams();
        formData.append('username', email);  // OAuth2 usa 'username' anche se è un'email
        formData.append('password', password);

        const response = await fetch(`/api/v1/auth/token`, {  // CORRETTO: già aveva /v1
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Errore durante il login';
            try {
                const errorData = await response.json();
                if (typeof errorData === 'object' && errorData !== null) {
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                }
            } catch (parseError) {
                // Se non riusciamo a parsare la risposta come JSON, usiamo il messaggio generico
                console.error('Errore nel parsing della risposta:', parseError);
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();

        // Salva il token nel localStorage
        localStorage.setItem('auth_token', data.access_token);

        // Ottieni i dati dell'utente
        await fetchUserData();

        // Ricarica la pagina per visualizzare la dashboard
        window.location.reload();
    } catch (error) {
        console.error('Errore login dashboard:', error);
        loginError.textContent = error.message || 'Errore durante il login. Riprova più tardi.';
        loginError.style.display = 'block';
    }
}

// Ottiene i dati dell'utente
async function fetchUserData() {
    try {
        const token = localStorage.getItem('auth_token');

        if (!token) {
            return null;
        }

        const response = await fetch(`/api/v1/auth/me`, {  // CORRETTO: già aveva /v1
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token non valido, effettua logout
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_data');
                return null;
            }
            throw new Error('Errore nel recupero dei dati utente');
        }

        const userData = await response.json();
        localStorage.setItem('user_data', JSON.stringify(userData));
        return userData;
    } catch (error) {
        console.error('Errore nel recupero dei dati utente:', error);
        return null;
    }
}

// Carica i dati dell'utente nella navbar
function loadUserInfo() {
    const userData = getCurrentUser();
    if (userData) {
        const userDisplay = document.getElementById('userDisplay');
        if (userDisplay) {
            userDisplay.textContent = userData.name;
        }
    }
}

// Carica la lista dei digital twins
async function loadDigitalTwins() {
    try {
        const response = await apiRequest('/digital-twins', 'GET');  // Usa apiRequest che ha già il prefisso corretto
        displayDigitalTwins(response);
    } catch (error) {
        console.error('Error loading digital twins:', error);
        showError('Failed to load digital twins: ' + error.message);
    }
}

// Mostra i digital twins nella lista
function displayDigitalTwins(digitalTwins) {
    const container = document.getElementById('digitalTwinsList');

    if (!digitalTwins || digitalTwins.length === 0) {
        container.innerHTML = `
            <div class="text-center p-3">
                <p class="text-muted">No digital twins found</p>
                <button class="btn btn-primary btn-sm" onclick="showCreateDtModal()">Create your first Digital Twin</button>
            </div>
        `;
        return;
    }

    const items = digitalTwins.map(dt => `
        <a href="#" class="list-group-item list-group-item-action" onclick="loadDigitalTwinDetails('${dt.id}')">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${dt.name}</h6>
                <small class="text-muted">${dt.digital_replica?.last_updated ? new Date(dt.digital_replica.last_updated).toLocaleDateString() : 'N/A'}</small>
            </div>
            <p class="mb-1 text-truncate">${dt.device_type || 'No type specified'}</p>
            <small class="text-muted">Sensori: ${dt.compatible_sensors?.length || 0}</small>
        </a>
    `).join('');

    container.innerHTML = items;
}

// Carica i dettagli di un digital twin
async function loadDigitalTwinDetails(dtId) {
    try {
        const response = await apiRequest(`/digital-twins/${dtId}`, 'GET');
        displayDigitalTwinDetails(response);

        // Segna come attivo nella lista
        document.querySelectorAll('#digitalTwinsList .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`#digitalTwinsList .list-group-item[onclick="loadDigitalTwinDetails('${dtId}')"]`)?.classList.add('active');
    } catch (error) {
        console.error('Error loading digital twin details:', error);
        showError('Failed to load digital twin details: ' + error.message);
    }
}

// Mostra i dettagli di un digital twin
function displayDigitalTwinDetails(dt) {
    const container = document.getElementById('digitalTwinDetails');

    const sensorDataHtml = dt.digital_replica?.sensor_data ?
        Object.keys(dt.digital_replica.sensor_data).map(sensorType => {
            const data = dt.digital_replica.sensor_data[sensorType];
            const lastValue = data && data.length > 0 ? data[data.length - 1] : null;
            return `
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">${sensorType}</h6>
                            <p class="card-text">
                                ${lastValue ?
                    `<strong>${lastValue.value}</strong> ${lastValue.unit_measure}<br>
                                     <small class="text-muted">${new Date(lastValue.timestamp).toLocaleString()}</small>`
                    : 'No data available'}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }).join('') : '<p class="text-muted">No sensor data available</p>';

    container.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">${dt.name}</h5>
            <div class="btn-group">
                <button class="btn btn-outline-success btn-sm" onclick="generateRandomData('${dt.id}')">
                    <i class="bi bi-arrow-clockwise"></i> Generate Data
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteDigitalTwin('${dt.id}')">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </div>
        <div class="card-body">
            <div class="row mb-4">
                <div class="col-md-6">
                    <h6>Details</h6>
                    <ul class="list-unstyled">
                        <li><strong>ID:</strong> ${dt.id}</li>
                        <li><strong>Device Type:</strong> ${dt.device_type}</li>
                        <li><strong>Device ID:</strong> ${dt.device_id || 'N/A'}</li>
                        <li><strong>Last Updated:</strong> ${dt.digital_replica?.last_updated ? new Date(dt.digital_replica.last_updated).toLocaleString() : 'Never'}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Compatible Sensors</h6>
                    ${dt.compatible_sensors && dt.compatible_sensors.length > 0 ? `
                        <div class="d-flex flex-wrap gap-1">
                            ${dt.compatible_sensors.map(sensor => `
                                <span class="badge bg-secondary">${sensor}</span>
                            `).join('')}
                        </div>
                    ` : '<p class="text-muted">No compatible sensors</p>'}
                </div>
            </div>
            
            <h6 class="mt-4">Current Sensor Data</h6>
            <div class="row">
                ${sensorDataHtml}
            </div>
            
            <div class="chart-container">
                <div id="sensorChart" style="width:100%; height:300px;"></div>
            </div>
        </div>
    `;

    // Genera il grafico se ci sono dati
    if (dt.digital_replica?.sensor_data) {
        createSensorChart(dt.digital_replica.sensor_data);
    }
}

// Crea il grafico dei sensori
function createSensorChart(sensorData) {
    const traces = [];

    Object.keys(sensorData).forEach(sensorType => {
        const data = sensorData[sensorType];
        if (data && data.length > 0) {
            traces.push({
                x: data.map(d => d.timestamp),
                y: data.map(d => d.value),
                type: 'scatter',
                mode: 'lines+markers',
                name: sensorType,
                line: { width: 2 }
            });
        }
    });

    if (traces.length > 0) {
        const layout = {
            title: 'Sensor Data Over Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Value' },
            margin: { t: 50, r: 50, b: 50, l: 50 }
        };

        Plotly.newPlot('sensorChart', traces, layout);
    } else {
        document.getElementById('sensorChart').innerHTML = '<p class="text-center text-muted">No data to display</p>';
    }
}

// Genera dati casuali per un digital twin
async function generateRandomData(dtId) {
    try {
        await apiRequest(`/digital-twins/${dtId}/generate-data`, 'POST');
        showSuccess('Random data generated successfully');

        // Ricarica i dettagli del digital twin
        loadDigitalTwinDetails(dtId);
    } catch (error) {
        console.error('Error generating random data:', error);
        showError('Failed to generate random data: ' + error.message);
    }
}

// Delete digital twin
async function deleteDigitalTwin(dtId) {
    if (!confirm('Are you sure you want to delete this Digital Twin? This action cannot be undone.')) {
        return;
    }

    try {
        await apiRequest(`/digital-twins/${dtId}`, 'DELETE');

        // Clear details and reload list
        document.getElementById('digitalTwinDetails').innerHTML = `
            <div class="card-body text-center">
                <p class="card-text">Select a Digital Twin from the list to view details</p>
            </div>
        `;

        loadDigitalTwins();
        showSuccess('Digital Twin deleted successfully');
    } catch (error) {
        console.error('Error deleting digital twin:', error);
        showError('Failed to delete digital twin: ' + error.message);
    }
}

// Show success message
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// Show error message
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}