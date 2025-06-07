document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const loginButton = document.getElementById('loginButton');
    const loadingIndicator = document.getElementById('loadingIndicator');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        
        errorMessage.style.display = 'none';
        
        loginButton.disabled = true;
        loadingIndicator.style.display = 'block';
        
        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                
                window.location.href = '/achievements';
                
            } else {
                showError(data.detail || 'Login failed');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            showError('Network error. Please try again.');
        } finally {
            loginButton.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    if (localStorage.getItem('access_token')) {
        fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/achievements';
            }
        })
        .catch(error => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        });
    }
});