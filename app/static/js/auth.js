// auth.js - Authentication management

document.addEventListener('DOMContentLoaded', function () {
    // DOM element references
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegisterFormBtn = document.getElementById('showRegisterForm');
    const registerSubmitBtn = document.getElementById('registerSubmit');
    const loginErrorAlert = document.getElementById('loginError');
    const registerErrorAlert = document.getElementById('registerError');

    // Check if user is already logged in
    checkAuthStatus();

    // Event listeners
    if (loginForm) {
        // Capture form submit to handle it with JavaScript
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault(); // Important: prevents normal submit
            handleLogin();
        });
    }

    if (showRegisterFormBtn) {
        showRegisterFormBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
            registerModal.show();
        });
    }

    if (registerSubmitBtn) {
        registerSubmitBtn.addEventListener('click', handleRegistration);
    }

    // Add debug button
    addDebugButton();
});

// Adds a debug button on the login page
function addDebugButton() {
    const loginContainer = document.querySelector('.login-container');
    if (!loginContainer) return;

    const debugContainer = document.createElement('div');
    debugContainer.className = 'mt-4 p-3 border rounded bg-light';
    debugContainer.innerHTML = `
        <h5>Debug OAuth2</h5>
        <p>Use this form to directly test the OAuth2 endpoint:</p>
        <form id="debugLoginForm">
            <div class="mb-3">
                <label class="form-label">Username (email)</label>
                <input type="text" id="debug_username" name="username" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" id="debug_password" name="password" class="form-control" required>
            </div>
            <button type="button" id="debugLoginBtn" class="btn btn-warning">Login with Fetch API</button>
        </form>
        <div class="mt-3">
            <button id="testTokenBtn" class="btn btn-info">Test token</button>
            <pre id="testTokenResult" class="mt-2 p-2 bg-dark text-light" style="display:none;"></pre>
        </div>
    `;

    loginContainer.appendChild(debugContainer);

    // Listener for debug login button
    document.getElementById('debugLoginBtn').addEventListener('click', async function () {
        const username = document.getElementById('debug_username').value;
        const password = document.getElementById('debug_password').value;
        const result = document.getElementById('testTokenResult');
        result.style.display = 'block';

        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            // FIXED: Use correct URL with /api/v1 prefix
            const response = await fetch('/api/v1/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            const data = await response.json();
            result.textContent = JSON.stringify(data, null, 2);

            if (data.access_token) {
                localStorage.setItem('auth_token', data.access_token);
                result.textContent += "\n\nToken saved in localStorage!";

                // Add a button to go to dashboard
                const goToDashboardBtn = document.createElement('button');
                goToDashboardBtn.className = 'btn btn-success mt-2';
                goToDashboardBtn.textContent = 'Go to Dashboard';
                goToDashboardBtn.addEventListener('click', function () {
                    window.location.href = '/api/v1/dashboard';
                });

                result.parentNode.appendChild(goToDashboardBtn);
            }
        } catch (error) {
            result.textContent = `Error: ${error.message}`;
        }
    });

    // Listener for test token button
    document.getElementById('testTokenBtn').addEventListener('click', async function () {
        const result = document.getElementById('testTokenResult');
        result.style.display = 'block';

        try {
            // FIXED: Use correct URL with /api/v1 prefix
            const response = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
                }
            });

            const data = await response.json();
            result.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            result.textContent = `Error: ${error.message}`;
        }
    });
}

// Handles login
async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorContainer = document.getElementById('loginError');

    try {
        errorContainer.style.display = 'none';

        // OAuth2 requires data in "application/x-www-form-urlencoded" format
        const formData = new URLSearchParams();
        formData.append('username', email);  // OAuth2 uses 'username' even if it's an email
        formData.append('password', password);

        console.log('Sending login with formData:', formData.toString());

        // FIXED: Use correct URL with /api/v1 prefix
        const response = await fetch('/api/v1/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Error during login';
            try {
                const errorData = await response.json();
                console.log('Login error response:', errorData);
                if (typeof errorData === 'object' && errorData !== null) {
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                }
            } catch (parseError) {
                // If we can't parse the response as JSON, use the generic message
                console.error('Error parsing response:', parseError);
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('Login success response:', data);

        // Save token in localStorage
        localStorage.setItem('auth_token', data.access_token);

        // Get user data
        await fetchUserData();

        // Redirect to dashboard
        window.location.href = '/api/v1/dashboard';
    } catch (error) {
        console.error('Login error:', error);
        errorContainer.textContent = error.message || 'Error during login. Try again later.';
        errorContainer.style.display = 'block';
    }
}

// Handles registration
async function handleRegistration() {
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    // Validation
    if (password.length < 8) {
        showRegisterError('Password must be at least 8 characters long');
        return;
    }

    try {
        // FIXED: Use correct URL with /api/v1 prefix
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });

        if (!response.ok) {
            let errorMessage = 'Error during registration';
            try {
                const errorData = await response.json();
                if (typeof errorData === 'object' && errorData !== null) {
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                }
            } catch (parseError) {
                console.error('Error parsing response:', parseError);
            }
            throw new Error(errorMessage);
        }

        // Close the modal
        const registerModal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
        registerModal.hide();

        // Fill in the login form
        document.getElementById('email').value = email;
        document.getElementById('password').value = password;

        // Show success message
        showSuccessMessage('Registration completed successfully! You can now log in.');
    } catch (error) {
        console.error('Registration error:', error);
        showRegisterError(error.message || 'Error during registration. Try again later.');
    }
}

// Get user data
async function fetchUserData() {
    try {
        const token = localStorage.getItem('auth_token');

        if (!token) {
            return null;
        }

        // FIXED: Use correct URL with /api/v1 prefix
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Invalid token, perform logout
                logout();
                return null;
            }
            throw new Error('Error retrieving user data');
        }

        const userData = await response.json();
        localStorage.setItem('user_data', JSON.stringify(userData));
        return userData;
    } catch (error) {
        console.error('Error retrieving user data:', error);
        return null;
    }
}

// Logout
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/api/v1/login';
}

// Check authentication status
function checkAuthStatus() {
    const token = localStorage.getItem('auth_token');
    const currentPath = window.location.pathname;

    // If we're on the login page and the user is already authenticated, redirect to dashboard
    if (currentPath === '/api/v1/login' && token) {
        window.location.href = '/api/v1/dashboard';
        return;
    }

    // If we're on another page but the user is not authenticated, redirect to login
    if (currentPath !== '/api/v1/login' && !token && !currentPath.includes('/api/v1/static/')) {
        window.location.href = '/api/v1/login';
        return;
    }
}

// Function to show login errors
function showLoginError(message) {
    const errorAlert = document.getElementById('loginError');
    errorAlert.textContent = message;
    errorAlert.style.display = 'block';
}

// Function to show registration errors
function showRegisterError(message) {
    const errorAlert = document.getElementById('registerError');
    errorAlert.textContent = message;
    errorAlert.style.display = 'block';
}

// Function to show success messages
function showSuccessMessage(message) {
    // Create a bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insert the alert at the beginning of the container
    const container = document.querySelector('.login-container');
    container.insertBefore(alertDiv, container.firstChild);

    // Automatically remove the alert after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}