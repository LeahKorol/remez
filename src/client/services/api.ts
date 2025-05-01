
import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL, // Default to localhost if not specified
  withCredentials: true, // This is important for cookies to be sent with requests
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add request interceptor to include credentials
api.interceptors.request.use(
  (config) => {
    // Make sure credentials are always sent
    config.withCredentials = true;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;
    
    if (response) {
      // Log detailed error information
      console.error('API Error:', {
        status: response.status,
        statusText: response.statusText,
        data: response.data,
        url: response.config?.url
      });
      
      if (response.status === 401) {
        // Handle 401 Unauthorized - could redirect to login or clear local auth state
        window.location.href = '/login';
      }
    } else {
      // Network error or other error that didn't come from the server
      console.error('Network Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
