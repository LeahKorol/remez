import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { getAuth, 
         GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";

// The web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAkV5g2KHDs2A8Lc8FzXDSnyvUSqrO3rpU",
  authDomain: "remez-ccf2d.firebaseapp.com",
  projectId: "remez-ccf2d",
  storageBucket: "remez-ccf2d.firebasestorage.app",
  messagingSenderId: "196822706306",
  appId: "1:196822706306:web:585d5833b7713d5b106c9b",
  measurementId: "G-RMKPP8SHD6"
};

  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const db = getFirestore(app);

export { auth, provider, db };