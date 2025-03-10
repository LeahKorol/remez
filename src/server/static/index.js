import { auth } from "./firebase-config.js";
import { authSignInWithGoogle, authSignUpWithGoogle, authSignInWithEmail, authCreateAccountWithEmail, resetPassword } from "./login-auth.js";

// UI elements
const signOutButtonEl = document.getElementById("sign-out-btn");

// Event listeners for sign out
signOutButtonEl.addEventListener("click", authSignOut);

// Sign-out function
function authSignOut() {
    signOut(auth).then(() => {
        console.log("User signed out");
    }).catch((error) => {
        console.error(error.message);
    });
}
