import axios from "axios";
import { createBrowserHistory } from "history";

const history = createBrowserHistory();

const axiosInstance = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
});

// interceptor for handling 500 errors globally
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // if the error is a 500, redirect to the 500 error page
    if (error.response?.status === 500 || !error.response) {
      history.push("/500");
      window.location.reload(); // force reload to ensure the error page is displayed
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
