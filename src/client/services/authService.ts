import api from './api';
import { toast } from 'sonner';

interface LoginCredentials {
  email: string;
  password: string;
}

export const authService = {
  // התחברות למערכת (Django)
  async login(credentials: LoginCredentials): Promise<{ uid: string; email: string; username: string }> {
    try {
      // שליחת פרטי ההתחברות לשרת
      const response = await api.post('/api/v1/auth/login/', credentials, {
        withCredentials: true, // חובה כדי שהעוגיות של ה-JWT יישמרו
      });

      // קבלת מידע על המשתמש המחובר
      const { data } = await api.get('/api/v1/auth/user/', { withCredentials: true });

      return {
        uid: data.id,
        email: data.email,
        username: data.email.split('@')[0] // יצירת שם משתמש מהאימייל
      };

    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please check your credentials.');
      throw error;
    }
  },

  // התנתקות מהמערכת
  async logout(): Promise<void> {
    try {
      await api.post('/api/v1/auth/logout/', {}, { withCredentials: true });
      toast.success('Logged out successfully.');
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Logout failed.');
      throw error;
    }
  },

  // בדיקת משתמש נוכחי
  async getCurrentUser(): Promise<{ uid: string; email: string; username: string } | null> {
    try {
      const { data } = await api.get('/api/v1/auth/user/', { withCredentials: true });

      if (data) {
        return {
          uid: data.id,
          email: data.email,
          username: data.email.split('@')[0]
        };
      }

      return null;
    } catch (error) {
      return null;
    }
  }
};
