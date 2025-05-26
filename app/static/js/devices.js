// devices.js - Script per la pagina dei dispositivi (versione corretta)

document.addEventListener('DOMContentLoaded', function () {
    // Elementi DOM
    const devicesList = document.getElementById('devices-list');
    const refreshDevicesBtn = document.getElementById('refresh-devices-btn');
    const deviceTypeDropdown = document.getElementById('device-type-dropdown');
    const attrNameDropdown = document.getElementById('attr-name-dropdown');
    const attrValueInput = document.getElementById('attr-value-input');
    const attrUnitDisplay = document.getElementById('attr-unit-display');
    const addAttrBtn = document.getElementById('add-attr-btn');
    const attributesList = document.getElementById('attributes-list');
    const createDeviceForm = document.getElementById('create-device-form');
    const ownerIdInput = document.getElementById('owner-id-input');

    // Attributi correnti del dispositivo
    window.currentAttributes = {};

    // Carica liste iniziali
    loadDevicesList();
    loadDeviceTypes();
    loadUsersList();

    // Event listeners
    refreshDevicesBtn.addEventListener('click', loadDevicesList);
    deviceTypeDropdown.addEventListener('change', onDeviceTypeChange);
    attrNameDropdown.addEventListener('change', onAttrNameChange);
    addAttrBtn.addEventListener('click', addAttribute);

    // Funzione per caricare la lista dei dispositivi
    async function loadDevicesList() {
        try {
            const devices = await apiRequest('/devices/');

            // Pulisci la lista
            devicesList.innerHTML = '';

            if (devices.length === 0) {
                devicesList.innerHTML = '<div class="alert alert-info">Nessun dispositivo trovato.</div>';
                return;
            }

            // Aggiungi ogni dispositivo alla lista
            devices.forEach(device => {
                const listItem = document.createElement('a');
                listItem.href = '#';
                listItem.className = 'list-group-item list-group-item-action';
                listItem.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${device.name}</h5>
                        <small>${device.device_type || device.template_id || 'Generic'}</small>
                    </div>
                    <p class="mb-1">ID: ${device.id}</p>
                    ${device.owner_id ? `<small>Proprietario: ${device.owner_id}</small><br>` : ''}
                    ${device.digital_twin_id ? `<small>Digital Twin: ${device.digital_twin_id}</small>` : ''}
                `;

                // Evento per visualizzare i dettagli del dispositivo
                listItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    showDeviceDetails(device.id);
                });

                devicesList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Errore nel caricamento dei dispositivi:', error);
            showError('Errore nel caricamento dei dispositivi: ' + error.message);
        }
    }

    // Funzione per caricare la lista degli utenti
    async function loadUsersList() {
        try {
            const users = await apiRequest('/users/');

            // Se la lista utenti è vuota, crea un utente di esempio
            if (users.length === 0) {
                await apiRequest('/users/', 'POST', {
                    name: "Utente Demo",
                    email: "demo@example.com"
                });
            }

            // Aggiorna il campo input owner_id con il suggerimento
            if (ownerIdInput) {
                const updatedUsers = await apiRequest('/users/');
                if (updatedUsers.length > 0) {
                    ownerIdInput.placeholder = `Es: ${updatedUsers[0].id}`;
                }
            }
        } catch (error) {
            console.error('Errore nel caricamento degli utenti:', error);
        }
    }

    // Funzione per caricare i tipi di dispositivo
    async function loadDeviceTypes() {
        try {
            const sensorTypes = await apiRequest('/sensors/types');

            // Pulisci il dropdown
            deviceTypeDropdown.innerHTML = '<option value="" selected disabled>Seleziona un tipo di dispositivo...</option>';

            // Aggiungi ogni tipo al dropdown
            sensorTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                deviceTypeDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento dei tipi di dispositivo:', error);
        }
    }

    // Funzione chiamata quando cambia il tipo di dispositivo
    async function onDeviceTypeChange() {
        const deviceType = deviceTypeDropdown.value;

        if (!deviceType) {
            attrNameDropdown.innerHTML = '<option value="" selected disabled>Seleziona attributo...</option>';
            return;
        }

        try {
            // Ottieni i sensori compatibili
            const compatibilityData = await apiRequest(`/sensors/compatibility?device_type=${deviceType}`);
            const compatibleSensors = compatibilityData.compatible_sensors || [];

            // Aggiorna il dropdown degli attributi
            attrNameDropdown.innerHTML = '<option value="" selected disabled>Seleziona attributo...</option>';

            compatibleSensors.forEach(sensor => {
                const option = document.createElement('option');
                option.value = sensor;
                option.textContent = sensor;
                attrNameDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento degli attributi compatibili:', error);
        }
    }

    // Funzione chiamata quando cambia l'attributo selezionato
    async function onAttrNameChange() {
        const attrName = attrNameDropdown.value;

        if (!attrName) {
            attrUnitDisplay.textContent = '';
            return;
        }

        try {
            // Ottieni i dettagli del sensore
            const sensorDetails = await apiRequest(`/sensors/types/${attrName}`);

            if (sensorDetails && sensorDetails.details) {
                const details = sensorDetails.details;

                // Visualizza l'unità di misura
                if (details.unitMeasure && details.unitMeasure.length > 0) {
                    attrUnitDisplay.textContent = `Unità: ${details.unitMeasure[0]}`;
                } else {
                    attrUnitDisplay.textContent = 'Unità: N/A';
                }
            } else {
                attrUnitDisplay.textContent = '';
            }
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli del sensore:', error);
        }
    }

    // Funzione per aggiungere un attributo
    function addAttribute() {
        const attrName = attrNameDropdown.value;
        const attrValue = parseFloat(attrValueInput.value);

        if (!attrName) {
            showError('Seleziona un attributo');
            return;
        }

        if (isNaN(attrValue)) {
            showError('Inserisci un valore numerico valido');
            return;
        }

        // Ottieni l'unità di misura
        let unitMeasure = '';
        const unitText = attrUnitDisplay.textContent;
        if (unitText && unitText !== 'Unità: N/A') {
            const match = unitText.match(/Unità: (.+)/);
            if (match) {
                unitMeasure = match[1];
            }
        }

        // Aggiungi alla lista degli attributi
        currentAttributes[attrName] = {
            value: attrValue,
            unit_measure: unitMeasure
        };

        // Aggiorna la lista visualizzata
        updateAttributesList();

        // Resetta i campi
        attrNameDropdown.value = '';
        attrValueInput.value = '';
        attrUnitDisplay.textContent = '';
    }

    // Funzione per aggiornare la lista degli attributi visualizzata
    function updateAttributesList() {
        attributesList.innerHTML = '';

        const attrNames = Object.keys(currentAttributes);

        if (attrNames.length === 0) {
            attributesList.innerHTML = '<div class="alert alert-info">Nessun attributo aggiunto.</div>';
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'list-group';

        attrNames.forEach(name => {
            const attr = currentAttributes[name];

            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            li.innerHTML = `
                <div>
                    <strong>${name}</strong>: ${attr.value} ${attr.unit_measure}
                </div>
                <button type="button" class="btn btn-sm btn-danger remove-attr" data-attr="${name}">
                    <i class="bi bi-trash"></i> Rimuovi
                </button>
            `;

            ul.appendChild(li);
        });

        attributesList.appendChild(ul);

        // Aggiungi event listeners per i pulsanti di rimozione
        document.querySelectorAll('.remove-attr').forEach(btn => {
            btn.addEventListener('click', e => {
                const attrName = e.currentTarget.getAttribute('data-attr');
                delete currentAttributes[attrName];
                updateAttributesList();
            });
        });
    }

    // Funzione per rigenerare API key
    async function regenerateApiKey(deviceId) {
        try {
            const result = await apiRequest(`/devices/regenerate-api-key?device_id=${deviceId}`, 'POST');
            return result.api_key;
        } catch (error) {
            console.error('Errore rigenerazione API key:', error);
            throw error;
        }
    }

    // Funzione per mostrare i dettagli di un dispositivo
    async function showDeviceDetails(deviceId) {
        try {
            const device = await apiRequest(`/devices/${deviceId}`);

            // Ottieni i dettagli del digital twin associato, se presente
            let digitalTwin = null;
            if (device.digital_twin_id) {
                digitalTwin = await apiRequest(`/digital-twins/${device.digital_twin_id}`);
            }

            // Prepara il contenuto del modal
            const modalContent = document.getElementById('device-details-content');

            let attributesHtml = '<p>Nessun attributo definito.</p>';
            if (device.attributes && Object.keys(device.attributes).length > 0) {
                attributesHtml = '<ul class="list-group">';

                for (const [attrName, attr] of Object.entries(device.attributes)) {
                    attributesHtml += `
                        <li class="list-group-item">
                            <strong>${attrName}</strong>: ${attr.value} ${attr.unit_measure || ''}
                        </li>
                    `;
                }

                attributesHtml += '</ul>';
            }

            let digitalTwinHtml = '<p>Nessun Digital Twin associato.</p>';
            if (digitalTwin) {
                digitalTwinHtml = `
                    <div class="card mt-3">
                        <div class="card-header">
                            <h5>Digital Twin: ${digitalTwin.name}</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>ID:</strong> ${digitalTwin.id}</p>
                            <p><strong>Ultimo aggiornamento:</strong> ${formatDateTime(digitalTwin.digital_replica?.last_updated || null)}</p>
                            
                            <h6>Sensori compatibili:</h6>
                            <ul>
                                ${digitalTwin.compatible_sensors.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                            
                            <div class="text-end">
                                <a href="/api/v1/dashboard?dt=${digitalTwin.id}" class="btn btn-primary">
                                    Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                `;
            }

            // Sezione per API Key con pulsante di copia e rigenerazione
            const apiKeyHtml = `
                <div class="card mt-3">
                    <div class="card-header">
                        <h5>API Key</h5>
                    </div>
                    <div class="card-body">
                        <div class="input-group mb-3">
                            <input type="text" id="api-key-display" class="form-control" 
                                value="${device.api_key || ''}" 
                                placeholder="No API key" readonly>
                            <button class="btn btn-outline-secondary" type="button" id="copy-api-key-btn">
                                Copia
                            </button>
                        </div>
                        <div class="d-flex justify-content-end">
                            <button class="btn btn-warning" id="regenerate-api-key-btn">
                                Rigenera API Key
                            </button>
                        </div>
                        <div class="alert alert-info mt-3">
                            <small>Questa API key è necessaria per autenticare il dispositivo quando invia dati al digital twin.</small>
                        </div>
                    </div>
                </div>
            `;

            modalContent.innerHTML = `
                <div class="container-fluid">
                    <h3>${device.name}</h3>
                    <p><strong>ID:</strong> ${device.id}</p>
                    <p><strong>Tipo:</strong> ${device.device_type || device.template_id || 'Generic'}</p>
                    <p>
                        <strong>Proprietario:</strong> 
                        ${device.owner_id ? device.owner_id : 'Nessun proprietario'}
                    </p>
                    
                    ${apiKeyHtml}
                    
                    <h5 class="mt-4">Attributi:</h5>
                    ${attributesHtml}
                    
                    <h5 class="mt-4">Digital Twin:</h5>
                    ${digitalTwinHtml}
                    
                    <div class="d-flex justify-content-end mt-3">
                        <button class="btn btn-danger me-2" id="delete-device-btn" data-id="${device.id}">
                            Elimina Dispositivo
                        </button>
                    </div>
                </div>
            `;

            // Mostra il modal
            const modal = new bootstrap.Modal(document.getElementById('device-details-modal'));
            modal.show();

            // Aggiungi listener per il pulsante di copia API key
            const copyApiKeyBtn = document.getElementById('copy-api-key-btn');
            if (copyApiKeyBtn) {
                copyApiKeyBtn.addEventListener('click', () => {
                    const apiKeyInput = document.getElementById('api-key-display');
                    apiKeyInput.select();
                    document.execCommand('copy');
                    showSuccess('API Key copiata negli appunti!');
                });
            }

            // Aggiungi listener per il pulsante di rigenerazione API key
            const regenerateApiKeyBtn = document.getElementById('regenerate-api-key-btn');
            if (regenerateApiKeyBtn) {
                regenerateApiKeyBtn.addEventListener('click', async () => {
                    if (confirm('Sei sicuro di voler rigenerare l\'API key? I dispositivi che utilizzano la chiave precedente non potranno più autenticarsi.')) {
                        try {
                            const newApiKey = await regenerateApiKey(device.id);
                            document.getElementById('api-key-display').value = newApiKey;
                            showSuccess('API Key rigenerata con successo!');
                        } catch (error) {
                            showError('Errore durante la rigenerazione dell\'API key');
                        }
                    }
                });
            }

            // Aggiungi listener per il pulsante di eliminazione
            document.getElementById('delete-device-btn').addEventListener('click', async () => {
                if (confirm('Sei sicuro di voler eliminare questo dispositivo? Questa azione non può essere annullata.')) {
                    try {
                        await apiRequest(`/devices/${device.id}`, 'DELETE');
                        modal.hide();
                        showSuccess('Dispositivo eliminato con successo!');
                        loadDevicesList();
                    } catch (error) {
                        console.error('Errore nell\'eliminazione del dispositivo:', error);
                    }
                }
            });
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli del dispositivo:', error);
            showError('Errore nel caricamento dei dettagli del dispositivo: ' + error.message);
        }
    }

    // Funzione per mostrare messaggi di successo
    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Funzione per mostrare messaggi di errore
    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Esponi le funzioni globalmente per uso da devices.html
    window.loadDevicesList = loadDevicesList;
    window.showDeviceDetails = showDeviceDetails;
});