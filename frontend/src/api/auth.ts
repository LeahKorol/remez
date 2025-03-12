import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/login/";

export const loginUser = async (email: string, password: string) => {
    try {
        const response = await axios.post(API_URL, { email, password });
        return response.data;  
    } catch (error) {
        throw new Error("Login failed");
    }
};
