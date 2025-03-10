import { auth, provider } from "./firebase-config.js";
import { createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithPopup,
    sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";

const signInWithGoogleButtonEl = document.getElementById("sign-in-with-google-btn");
const signUpWithGoogleButtonEl = document.getElementById("sign-up-with-google-btn");
const emailInputEl = document.getElementById("email-input");
const passwordInputEl = document.getElementById("password-input");
const signInButtonEl = document.getElementById("sign-in-btn");
const createAccountButtonEl = document.getElementById("create-account-btn");
const emailForgotPasswordEl = document.getElementById("email-forgot-password");
const forgotPasswordButtonEl = document.getElementById("forgot-password-btn");

const errorMsgEmail = document.getElementById("email-error-message");
const errorMsgPassword = document.getElementById("password-error-message");
const errorMsgGoogleSignIn = document.getElementById("google-signin-error-message");

if (signInWithGoogleButtonEl && signInButtonEl) {
    signInWithGoogleButtonEl.addEventListener("click", authSignInWithGoogle);
    signInButtonEl.addEventListener("click", authSignInWithEmail);
}

if (createAccountButtonEl) {
    createAccountButtonEl.addEventListener("click", authCreateAccountWithEmail);
}

if (signUpWithGoogleButtonEl) {
    signUpWithGoogleButtonEl.addEventListener("click", authSignUpWithGoogle);
}

if (forgotPasswordButtonEl) {
    forgotPasswordButtonEl.addEventListener("click", resetPassword);
}

// Functions for authentication
async function authSignInWithGoogle() {
    provider.setCustomParameters({ 'prompt': 'select_account' });
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        const email = user.email;

        if (!email) {
            throw new Error('No email address returned');
        }

        const idToken = await user.getIdToken();
        loginUser(user, idToken);
    } catch (error) {
        handleLogging(error, 'Error during sign-in with Google');
    }
}

async function authSignUpWithGoogle() {
    provider.setCustomParameters({ 'prompt': 'select_account' });
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        const email = user.email;

        const idToken = await user.getIdToken();
        loginUser(user, idToken);
    } catch (error) {
        console.error("Error during Google signup:", error.message);
    }
}

function authSignInWithEmail() {
    const email = emailInputEl.value;
    const password = passwordInputEl.value;

    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            user.getIdToken().then(function(idToken) {
                loginUser(user, idToken);
            });
        })
        .catch((error) => {
            const errorCode = error.code;
            if (errorCode === "auth/invalid-email") {
                errorMsgEmail.textContent = "Invalid email";
            } else if (errorCode === "auth/invalid-credential") {
                errorMsgPassword.textContent = "Login failed - invalid email or password";
            }
        });
}

function authCreateAccountWithEmail() {
    const email = emailInputEl.value;
    const password = passwordInputEl.value;

    createUserWithEmailAndPassword(auth, email, password)
        .then(async (userCredential) => {
            const user = userCredential.user;
            user.getIdToken().then(function(idToken) {
                loginUser(user, idToken);
            });
        })
        .catch((error) => {
            const errorCode = error.code;
            if (errorCode === "auth/invalid-email") {
                errorMsgEmail.textContent = "Invalid email";
            } else if (errorCode === "auth/weak-password") {
                errorMsgPassword.textContent = "Password too weak";
            } else if (errorCode === "auth/email-already-in-use") {
                errorMsgEmail.textContent = "Email already in use";
            }
        });
}

function resetPassword() {
    const emailToReset = emailForgotPasswordEl.value;
    sendPasswordResetEmail(auth, emailToReset)
        .then(() => {
            const resetFormView = document.getElementById("reset-password-view");
            const resetSuccessView = document.getElementById("reset-password-confirmation-page");

            resetFormView.style.display = "none";
            resetSuccessView.style.display = "block";
        })
        .catch((error) => {
            console.error("Error resetting password:", error.message);
        });
}

function loginUser(user, idToken) {
    fetch('/api/sessionLogin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${idToken}`
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            'idToken': idToken
        })
    }).then(response => {
        if (response.ok) {
            window.location.href = '/dashboard';
        } else {
            console.error('Failed to login');
        }
    }).catch(error => {
        console.error('Error with Fetch operation:', error);
    });
}

function handleLogging(error, message) {
    console.error(message, error);
}
