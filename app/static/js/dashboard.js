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
    document.querySelector('main .container').appendChild(loginContainer);

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

        const response = await fetch(`/api/v1/auth/token`, {
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

        const response = await fetch(`/api/v1/auth/me`, {
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
        const response = await apiRequest('/digital_twins', 'GET');
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
                <small class="text-muted">${new Date(dt.created_at).toLocaleDateString()}</small>
            </div>
            <p class="mb-1 text-truncate">${dt.description || 'No description'}</p>
        </a>
    `).join('');

    container.innerHTML = items;
}

// Carica i dettagli di un digital twin
async function loadDigitalTwinDetails(dtId) {
    try {
        const response = await apiRequest(`/digital_twins/${dtId}`, 'GET');
        displayDigitalTwinDetails(response);
    } catch (error) {
        console.error('Error loading digital twin details:', error);
        showError('Failed to load digital twin details: ' + error.message);
    }
}

// Mostra i dettagli di un digital twin
function displayDigitalTwinDetails(dt) {
    const container = document.getElementById('digitalTwinDetails');

    container.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">${dt.name}</h5>
            <div class="btn-group">
                <button class="btn btn-outline-primary btn-sm" onclick="editDigitalTwin('${dt.id}')">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteDigitalTwin('${dt.id}')">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </div>
        <div class="card-body">
            <p class="card-text">${dt.description || 'No description'}</p>
            
            <h6 class="mt-4">Details</h6>
            <ul class="list-unstyled">
                <li><strong>ID:</strong> ${dt.id}</li>
                <li><strong>Created:</strong> ${new Date(dt.created_at).toLocaleString()}</li>
                <li><strong>Last Updated:</strong> ${new Date(dt.updated_at).toLocaleString()}</li>
            </ul>
            
            <h6 class="mt-4">Connected Devices</h6>
            <div id="connectedDevices">
                ${dt.devices && dt.devices.length > 0 ? `
                    <ul class="list-group">
                        ${dt.devices.map(device => `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                ${device.name}
                                <span class="badge bg-primary rounded-pill">${device.status || 'Unknown'}</span>
                            </li>
                        `).join('')}
                    </ul>
                ` : `
                    <p class="text-muted">No devices connected</p>
                    <button class="btn btn-outline-primary btn-sm" onclick="connectDevice('${dt.id}')">
                        <i class="bi bi-link"></i> Connect Device
                    </button>
                `}
            </div>
            
            <h6 class="mt-4">Telemetry</h6>
            <div id="telemetryChart" style="height: 300px;">
                <p class="text-muted text-center">Select a device to view telemetry data</p>
            </div>
        </div>
    `;
}

// Edit digital twin
async function editDigitalTwin(dtId) {
    try {
        const dt = await apiRequest(`/digital_twins/${dtId}`, 'GET');

        // Create and show modal
        const modalHtml = `
            <div class="modal fade" id="editDtModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit Digital Twin</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger" id="editDtError" style="display: none;"></div>
                            <form id="editDtForm">
                                <div class="mb-3">
                                    <label class="form-label">Name</label>
                                    <input type="text" class="form-control" id="editDtName" value="${dt.name}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" id="editDtDescription" rows="3">${dt.description || ''}</textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="saveDigitalTwin('${dt.id}')">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to document
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editDtModal'));
        modal.show();

        // Clean up modal after it's hidden
        document.getElementById('editDtModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    } catch (error) {
        console.error('Error loading digital twin for editing:', error);
        showError('Failed to load digital twin: ' + error.message);
    }
}

// Save digital twin changes
async function saveDigitalTwin(dtId) {
    const name = document.getElementById('editDtName').value;
    const description = document.getElementById('editDtDescription').value;
    const errorElement = document.getElementById('editDtError');

    if (!name) {
        errorElement.textContent = 'Name is required';
        errorElement.style.display = 'block';
        return;
    }

    try {
        await apiRequest(`/digital_twins/${dtId}`, 'PUT', {
            name,
            description
        });

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editDtModal'));
        modal.hide();

        // Reload data
        loadDigitalTwins();
        loadDigitalTwinDetails(dtId);

        showSuccess('Digital Twin updated successfully');
    } catch (error) {
        console.error('Error updating digital twin:', error);
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    }
}

// Delete digital twin
async function deleteDigitalTwin(dtId) {
    if (!confirm('Are you sure you want to delete this Digital Twin? This action cannot be undone.')) {
        return;
    }

    try {
        await apiRequest(`/digital_twins/${dtId}`, 'DELETE');

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

// Connect device to digital twin
function connectDevice(dtId) {
    // Create and show modal
    const modalHtml = `
        <div class="modal fade" id="connectDeviceModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Connect Device</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-danger" id="connectDeviceError" style="display: none;"></div>
                        <form id="connectDeviceForm">
                            <div class="mb-3">
                                <label class="form-label">Select Device</label>
                                <select class="form-select" id="deviceSelect">
                                    <option value="">Loading devices...</option>
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveDeviceConnection('${dtId}')">Connect</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('connectDeviceModal'));
    modal.show();

    // Load available devices
    loadAvailableDevices();

    // Clean up modal after it's hidden
    document.getElementById('connectDeviceModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// Load available devices for connection
async function loadAvailableDevices() {
    try {
        const devices = await apiRequest('/devices', 'GET');
        const select = document.getElementById('deviceSelect');

        if (!devices || devices.length === 0) {
            select.innerHTML = '<option value="">No devices available</option>';
            return;
        }

        select.innerHTML = `
            <option value="">Select a device...</option>
            ${devices.map(device => `
                <option value="${device.id}">${device.name}</option>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error loading devices:', error);
        document.getElementById('connectDeviceError').textContent = 'Failed to load devices: ' + error.message;
        document.getElementById('connectDeviceError').style.display = 'block';
    }
}

// Save device connection
async function saveDeviceConnection(dtId) {
    const deviceId = document.getElementById('deviceSelect').value;
    const errorElement = document.getElementById('connectDeviceError');

    if (!deviceId) {
        errorElement.textContent = 'Please select a device';
        errorElement.style.display = 'block';
        return;
    }

    try {
        await apiRequest(`/digital_twins/${dtId}/devices/${deviceId}`, 'POST');

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('connectDeviceModal'));
        modal.hide();

        // Reload digital twin details
        loadDigitalTwinDetails(dtId);

        showSuccess('Device connected successfully');
    } catch (error) {
        console.error('Error connecting device:', error);
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
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