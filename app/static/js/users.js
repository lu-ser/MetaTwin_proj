// users.js - Script per la pagina di gestione utenti

document.addEventListener('DOMContentLoaded', function () {
    // Elementi DOM
    const usersList = document.getElementById('users-list');
    const refreshUsersBtn = document.getElementById('refresh-users-btn');
    const createUserForm = document.getElementById('create-user-form');

    // Carica lista utenti al caricamento della pagina
    loadUsersList();

    // Event listeners
    refreshUsersBtn.addEventListener('click', loadUsersList);
    createUserForm.addEventListener('submit', createUser);

    // Funzione per caricare la lista degli utenti
    async function loadUsersList() {
        try {
            const users = await apiRequest('/users/');

            // Pulisci la lista
            usersList.innerHTML = '';

            if (users.length === 0) {
                usersList.innerHTML = '<div class="alert alert-info">Nessun utente trovato.</div>';
                return;
            }

            // Aggiungi ogni utente alla lista
            users.forEach(user => {
                const listItem = document.createElement('a');
                listItem.href = '#';
                listItem.className = 'list-group-item list-group-item-action';
                listItem.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${user.name}</h5>
                        <small>${user.email || 'Nessuna email'}</small>
                    </div>
                    <p class="mb-1">ID: ${user.id}</p>
                    <small>Dispositivi: ${user.devices?.length || 0}, Digital Twins: ${user.digital_twins?.length || 0}</small>
                `;

                // Evento per visualizzare i dettagli dell'utente
                listItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    showUserDetails(user.id);
                });

                usersList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Errore nel caricamento degli utenti:', error);
        }
    }

    // Funzione per creare un nuovo utente
    async function createUser(e) {
        e.preventDefault();

        const userName = document.getElementById('user-name-input').value.trim();
        const userEmail = document.getElementById('user-email-input').value.trim();

        if (!userName) {
            showError('Inserisci un nome per l\'utente');
            return;
        }

        // Prepara i dati dell'utente
        const userData = {
            name: userName
        };

        // Aggiungi email se specificata
        if (userEmail) {
            userData.email = userEmail;
        }

        try {
            // Crea l'utente
            await apiRequest('/users/', 'POST', userData);

            // Mostra messaggio di successo
            showSuccess('Utente creato con successo!');

            // Aggiorna la lista degli utenti
            loadUsersList();

            // Resetta il form
            createUserForm.reset();
        } catch (error) {
            console.error('Errore nella creazione dell\'utente:', error);
        }
    }

    // Funzione per mostrare i dettagli di un utente
    async function showUserDetails(userId) {
        try {
            const user = await apiRequest(`/users/${userId}`);

            // Ottieni i dispositivi dell'utente
            const devices = await apiRequest(`/users/${userId}/devices`);

            // Ottieni i digital twins dell'utente
            const digitalTwins = await apiRequest(`/users/${userId}/digital-twins`);

            // Prepara il contenuto del modal
            const modalContent = document.getElementById('user-details-content');

            // Lista dispositivi
            let devicesHtml = '<p>Nessun dispositivo associato.</p>';
            if (devices && devices.length > 0) {
                devicesHtml = '<ul class="list-group">';
                devices.forEach(device => {
                    devicesHtml += `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${device.name}</strong> (${device.device_type})
                                <br><small>ID: ${device.id}</small>
                            </div>
                            <a href="#" class="btn btn-sm btn-primary view-device" data-device-id="${device.id}">
                                Dettagli
                            </a>
                        </li>
                    `;
                });
                devicesHtml += '</ul>';
            }

            // Lista digital twins
            let digitalTwinsHtml = '<p>Nessun digital twin associato.</p>';
            if (digitalTwins && digitalTwins.length > 0) {
                digitalTwinsHtml = '<ul class="list-group">';
                digitalTwins.forEach(dt => {
                    digitalTwinsHtml += `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${dt.name}</strong> (${dt.device_type})
                                <br><small>ID: ${dt.id}</small>
                            </div>
                            <a href="/api/v1/dashboard?dt=${dt.id}" class="btn btn-sm btn-primary">
                                Dashboard
                            </a>
                        </li>
                    `;
                });
                digitalTwinsHtml += '</ul>';
            }

            modalContent.innerHTML = `
                <div class="container-fluid">
                    <h3>${user.name}</h3>
                    <p><strong>ID:</strong> ${user.id}</p>
                    <p><strong>Email:</strong> ${user.email || 'Nessuna email'}</p>
                    
                    <h5 class="mt-4">Dispositivi:</h5>
                    ${devicesHtml}
                    
                    <h5 class="mt-4">Digital Twins:</h5>
                    ${digitalTwinsHtml}
                    
                    <div class="d-flex justify-content-end mt-3">
                        <button class="btn btn-danger" id="delete-user-btn" data-id="${user.id}">
                            Elimina Utente
                        </button>
                    </div>
                </div>
            `;

            // Mostra il modal
            const modal = new bootstrap.Modal(document.getElementById('user-details-modal'));
            modal.show();

            // Aggiungi event listeners per i pulsanti di visualizzazione dispositivo
            document.querySelectorAll('.view-device').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const deviceId = e.currentTarget.getAttribute('data-device-id');

                    // Nascondi il modal corrente
                    modal.hide();

                    // Simula un click sul dispositivo nella pagina dispositivi
                    // (Questa è una soluzione temporanea; idealmente vorremmo aprire il modal direttamente)
                    setTimeout(() => {
                        window.location.href = '/api/v1/devices';
                        // In una versione più avanzata, potremmo usare i parametri URL per aprire automaticamente
                        // il dispositivo corretto nella pagina di destinazione
                    }, 500);
                });
            });

            // Aggiungi listener per il pulsante di eliminazione
            document.getElementById('delete-user-btn').addEventListener('click', async () => {
                if (confirm('Sei sicuro di voler eliminare questo utente? Questa azione non può essere annullata e rimuoverà anche tutti i dispositivi e digital twins associati.')) {
                    try {
                        await apiRequest(`/users/${user.id}`, 'DELETE');
                        modal.hide();
                        showSuccess('Utente eliminato con successo!');
                        loadUsersList();
                    } catch (error) {
                        console.error('Errore nell\'eliminazione dell\'utente:', error);
                    }
                }
            });
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli dell\'utente:', error);
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
});