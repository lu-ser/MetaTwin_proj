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

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Errore ${response.status}: ${response.statusText}`);
        }

        // Per DELETE, non c'è un corpo JSON
        if (method === 'DELETE') {
            return { success: true };
        }

        return await response.json();
    } catch (error) {
        showError(`Errore API: ${error.message}`);
        throw error;
    }
}

// Formatta data e ora
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return 'N/A';

    const date = new Date(dateTimeStr);
    return date.toLocaleString('it-IT');
}