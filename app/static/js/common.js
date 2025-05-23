// common.js - Funzioni comuni per tutte le pagine

// URL di base per le API
const API_BASE_URL = '/api/v1';

// Funzione per mostrare errori
function showError(message) {
    // Crea un alert di bootstrap
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Inserisci l'alert all'inizio del container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Elimina automaticamente l'alert dopo 5 secondi
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Funzione per le richieste API
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        // Aggiungi il token di autenticazione se disponibile nel localStorage
        const token = localStorage.getItem('auth_token');
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            // Se c'è un errore di autenticazione, reindirizza alla pagina di login
            if (response.status === 401) {
                // Solo se non siamo già sulla pagina di login
                if (!window.location.pathname.includes('/login')) {
                    localStorage.removeItem('auth_token');
                    localStorage.removeItem('user_data');
                    window.location.href = '/api/v1/login';
                    throw new Error('Sessione scaduta. Effettua nuovamente il login.');
                }
            }

            let errorMessage = `Errore ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (typeof errorData === 'object' && errorData !== null) {
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                }
            } catch (parseError) {
                console.error('Errore nel parsing della risposta di errore:', parseError);
            }
            throw new Error(errorMessage);
        }

        // Per DELETE, non c'è un corpo JSON
        if (method === 'DELETE') {
            return { success: true };
        }

        return await response.json();
    } catch (error) {
        console.error('Errore API:', error);
        const errorMessage = error.message || 'Si è verificato un errore durante la richiesta API';
        showError(`Errore API: ${errorMessage}`);
        throw error;
    }
}

// Formatta data e ora
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return 'N/A';

    const date = new Date(dateTimeStr);
    return date.toLocaleString('it-IT');
}

// Funzione per verificare se l'utente è autenticato
function isAuthenticated() {
    return localStorage.getItem('auth_token') !== null;
}

// Funzione per ottenere i dati dell'utente corrente
function getCurrentUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
}

// Funzione per il logout
function handleLogout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/api/v1/login';
}

// Aggiungi il pulsante di logout e le informazioni utente nella navbar
document.addEventListener('DOMContentLoaded', function () {
    // Non eseguire questa logica nella pagina di login
    if (window.location.pathname !== '/api/v1/login') {
        const navbarNav = document.getElementById('navbarNav');
        if (navbarNav) {
            const userData = getCurrentUser();

            // Crea l'elemento per le informazioni utente e logout
            const userNavItem = document.createElement('ul');
            userNavItem.className = 'navbar-nav ms-auto';

            if (userData) {
                userNavItem.innerHTML = `
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                            ${userData.name}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                            <li><a class="dropdown-item" href="/api/v1/profile">Profilo</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#" id="logoutBtn">Logout</a></li>
                        </ul>
                    </li>
                `;

                navbarNav.appendChild(userNavItem);

                // Aggiungi l'event listener per il logout
                document.getElementById('logoutBtn').addEventListener('click', function (e) {
                    e.preventDefault();
                    handleLogout();
                });
            }
        }
    }
});