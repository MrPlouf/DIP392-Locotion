document.addEventListener('DOMContentLoaded', () => {
    // Get references to the elements
    const loginTab = document.getElementById('login-tab');
    const signupTab = document.getElementById('signup-tab');
    const loginFormContent = document.getElementById('login-form-content');
    const signupFormContent = document.getElementById('signup-form-content');

    // Function to switch to Login view
    function showLogin() {
        // Update tab active states
        loginTab.classList.add('active');
        signupTab.classList.remove('active');

        // Update form visibility
        loginFormContent.classList.remove('hidden');
        signupFormContent.classList.add('hidden');
    }

    // Function to switch to Sign Up view
    function showSignUp() {
        // Update tab active states
        signupTab.classList.add('active');
        loginTab.classList.remove('active');

        // Update form visibility
        signupFormContent.classList.remove('hidden');
        loginFormContent.classList.add('hidden');
    }

    // Add event listeners to the tabs
    loginTab.addEventListener('click', showLogin);
    signupTab.addEventListener('click', showSignUp);

    // Initial state check (optional, default is Sign Up visible via HTML/CSS)
    // If you wanted Login to be the default, you'd call showLogin() here
    // and adjust the initial 'active' and 'hidden' classes in the HTML.
});