
import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000', // Default to localhost if not specified
  withCredentials: true, // This is important for cookies to be sent with requests
  headers: {
    'Content-Type': 'application/json',
  }
});

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;
    
    if (response && response.status === 401) {
      // Handle 401 Unauthorized - could redirect to login or clear local auth state
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default api;
