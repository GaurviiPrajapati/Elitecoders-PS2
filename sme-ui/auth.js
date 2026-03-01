// auth.js - Handles Authentication UI and Mock API requests

document.addEventListener('DOMContentLoaded', () => {
    // --- UI Toggles ---
    const loginPanel = document.getElementById('login-panel');
    const signupPanel = document.getElementById('signup-panel');
    const showSignupBtn = document.getElementById('show-signup');
    const showLoginBtn = document.getElementById('show-login');

    if (showSignupBtn && showLoginBtn) {
        showSignupBtn.addEventListener('click', () => {
            loginPanel.style.opacity = '0';
            loginPanel.style.transform = 'translateY(10px)';

            setTimeout(() => {
                loginPanel.classList.add('ui-hidden');
                signupPanel.classList.remove('ui-hidden');

                // Trigger reflow
                void signupPanel.offsetWidth;

                signupPanel.style.opacity = '1';
                signupPanel.style.transform = 'translateY(0)';
            }, 300);
        });

        showLoginBtn.addEventListener('click', () => {
            signupPanel.style.opacity = '0';
            signupPanel.style.transform = 'translateY(10px)';

            setTimeout(() => {
                signupPanel.classList.add('ui-hidden');
                loginPanel.classList.remove('ui-hidden');

                // Trigger reflow
                void loginPanel.offsetWidth;

                loginPanel.style.opacity = '1';
                loginPanel.style.transform = 'translateY(0)';
            }, 300);
        });

        // Initial setup for animation
        signupPanel.style.opacity = '0';
        signupPanel.style.transform = 'translateY(10px)';
        signupPanel.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

        loginPanel.style.opacity = '1';
        loginPanel.style.transform = 'translateY(0)';
        loginPanel.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    }


    // --- API Interactions ---

    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    // API Endpoints
    const API_BASE_URL = 'http://localhost:5000/api'; // Replace with your actual backend URL

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('login-username').value;
            const passwordInput = document.getElementById('login-password').value;
            const errorMsg = document.getElementById('login-error');
            const submitBtn = document.getElementById('login-submit-btn');

            errorMsg.textContent = '';
            submitBtn.textContent = 'Authenticating...';
            submitBtn.disabled = true;

            try {
                // Determine if input is email or username
                const isEmail = usernameInput.includes('@');
                const payload = isEmail ? { email: usernameInput, password: passwordInput }
                    : { username: usernameInput, password: passwordInput };

                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    // Save Token
                    localStorage.setItem('expertEaseToken', data.token || 'mock_token_for_now');
                    localStorage.setItem('expertEaseUser', JSON.stringify(data.user || { username: usernameInput }));

                    submitBtn.textContent = 'Success! Redirecting...';
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 500);
                } else {
                    throw new Error(data.message || 'Authentication failed');
                }
            } catch (error) {
                console.error('Login error:', error);

                // --- MOCK FALLBACK for UI testing without a real backend ---
                if (error.message === 'Failed to fetch') {
                    console.warn('Backend not detected. Proceeding with mock authentication for UI demonstration.');
                    localStorage.setItem('expertEaseToken', 'mock_token_123');
                    localStorage.setItem('expertEaseUser', JSON.stringify({ username: usernameInput }));
                    submitBtn.textContent = 'Mock Auth Success!';
                    setTimeout(() => window.location.href = 'index.html', 500);
                    return;
                }
                // -------------------------------------------------------------

                errorMsg.textContent = error.message;
                submitBtn.textContent = 'Sign In';
                submitBtn.disabled = false;
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('signup-username').value;
            const emailInput = document.getElementById('signup-email').value;
            const passwordInput = document.getElementById('signup-password').value;
            const errorMsg = document.getElementById('signup-error');
            const submitBtn = document.getElementById('signup-submit-btn');

            errorMsg.textContent = '';
            submitBtn.textContent = 'Creating Account...';
            submitBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: usernameInput,
                        email: emailInput,
                        password: passwordInput
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Save Token
                    localStorage.setItem('expertEaseToken', data.token || 'mock_token_for_now');
                    localStorage.setItem('expertEaseUser', JSON.stringify(data.user || { username: usernameInput, email: emailInput }));

                    submitBtn.textContent = 'Account Created!';
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 500);
                } else {
                    throw new Error(data.message || 'Registration failed');
                }
            } catch (error) {
                console.error('Registration error:', error);

                // --- MOCK FALLBACK for UI testing without a real backend ---
                if (error.message === 'Failed to fetch') {
                    console.warn('Backend not detected. Proceeding with mock registration for UI demonstration.');
                    localStorage.setItem('expertEaseToken', 'mock_token_123');
                    localStorage.setItem('expertEaseUser', JSON.stringify({ username: usernameInput, email: emailInput }));
                    submitBtn.textContent = 'Mock Registration Success!';
                    setTimeout(() => window.location.href = 'index.html', 500);
                    return;
                }
                // -------------------------------------------------------------

                errorMsg.textContent = error.message;
                submitBtn.textContent = 'Create Account';
                submitBtn.disabled = false;
            }
        });
    }
});
