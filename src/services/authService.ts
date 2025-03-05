
import api from './api';
import { toast } from 'sonner';
import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import { firebaseConfig } from '../config/firebase';

// Initialize Firebase if not already initialized
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

interface LoginCredentials {
  email: string;
  password: string;
}

export const authService = {
  // Login function using Firebase Auth and then getting a session cookie
  async login(credentials: LoginCredentials): Promise<{ uid: string; email: string; username: string }> {
    try {
      // 1. Login to Firebase to get ID token
      const userCredential = await firebase.auth().signInWithEmailAndPassword(
        credentials.email, 
        credentials.password
      );
      
      // 2. Get the ID token from Firebase
      const idToken = await userCredential.user?.getIdToken();
      
      if (!idToken || !userCredential.user) {
        throw new Error('Failed to get Firebase ID token');
      }

      // 3. Send token to backend to create session cookie
      await api.post('/sessionLogin', { idToken });
      
      // 4. Get user details from the /me endpoint
      const { data } = await api.get('/me');
      
      // 5. Return user data for the frontend
      return {
        uid: data.uid,
        email: credentials.email,
        username: credentials.email.split('@')[0] // Generate username from email for demo
      };
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please check your credentials.');
      throw error;
    }
  },

  // Logout function
  async logout(): Promise<void> {
    try {
      // Sign out from Firebase
      await firebase.auth().signOut();
      
      // Tell the backend to invalidate the session cookie
      await api.post('/sessionLogout');
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Logout failed');
      throw error;
    }
  },

  // Check if user is authenticated
  async getCurrentUser(): Promise<{ uid: string; email: string; username: string } | null> {
    try {
      const { data } = await api.get('/me');
      
      // If we successfully got user data, the user is authenticated
      if (data && data.uid) {
        // Get current Firebase user to get the email
        const currentUser = firebase.auth().currentUser;
        const email = currentUser?.email || `user-${data.uid}@example.com`;
        
        return {
          uid: data.uid,
          email: email,
          username: email.split('@')[0]
        };
      }
      
      return null;
    } catch (error) {
      // If 401 or other error, user is not authenticated
      return null;
    }
  }
};
