
import api from './api';
import { toast } from 'sonner';

interface LoginCredentials {
  email: string;
  password: string;
}

export const authService = {
  // Login function (in a real app would get idToken from Firebase first)
  async login(credentials: LoginCredentials): Promise<{ uid: string; email: string; username: string }> {
    try {
      // In a real implementation, we would:
      // 1. Authenticate with Firebase to get ID token
      // 2. Send that token to our backend
      
      // For demo purposes, we'll simulate this process
      const mockIdToken = "mock-firebase-id-token";
      
      await api.post('/sessionLogin', { idToken: mockIdToken });
      
      // Get user details from the /me endpoint
      const { data } = await api.get('/me');
      
      // Return user data for the frontend
      return {
        uid: data.uid,
        email: credentials.email, // The email would normally come from the /me response
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
      
      // In a real app, the /me endpoint would return more user details
      // For demo, we'll just use the uid and create dummy values
      return {
        uid: data.uid,
        email: `user-${data.uid}@example.com`, // Dummy email
        username: `user-${data.uid}` // Dummy username
      };
    } catch (error) {
      // If 401 or other error, user is not authenticated
      return null;
    }
  }
};
