class TokenService {
    constructor() {
        this.isRefreshing = false;
        this.refreshSubscribers = [];
    }

    getAccessToken() {
        return localStorage.getItem('token');
    }

    getRefreshToken() {
        return localStorage.getItem('refreshToken');
    }

    setTokens(accessToken, refreshToken = null) {
        localStorage.setItem('token', accessToken);
        if (refreshToken) {
            localStorage.setItem('refreshToken', refreshToken);
        }
    }

    clearTokens() {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
    }

    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/auth/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh: refreshToken
                })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.setTokens(data.access, data.refresh || refreshToken);
            return data.access;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    // Add request to queue while token is being refreshed
    addRefreshSubscriber(callback) {
        this.refreshSubscribers.push(callback);
    }

    // Execute all queued requests after token refresh
    onRefreshed(token) {
        this.refreshSubscribers.forEach(callback => callback(token));
        this.refreshSubscribers = [];
    }

    async handleTokenRefresh(originalRequest) {
        if (!this.isRefreshing) {
            this.isRefreshing = true;

            try {
                const newToken = await this.refreshAccessToken();
                this.isRefreshing = false;
                this.onRefreshed(newToken);
                
                // Retry original request with new token
                return this.executeRequest(originalRequest, newToken);
            } catch (error) {
                this.isRefreshing = false;
                this.onRefreshed(null);
                throw error;
            }
        }

        // If refresh is already in progress, queue this request
        return new Promise((resolve, reject) => {
            this.addRefreshSubscriber((token) => {
                if (token) {
                    this.executeRequest(originalRequest, token)
                        .then(resolve)
                        .catch(reject);
                } else {
                    reject(new Error('Token refresh failed'));
                }
            });
        });
    }

    async executeRequest(requestConfig, token = null) {
        const accessToken = token || this.getAccessToken();
        
        const config = {
            ...requestConfig,
            headers: {
                ...requestConfig.headers,
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        };

        return fetch(requestConfig.url, config);
    }
}

// Create singleton instance
const tokenService = new TokenService();

// Enhanced fetchWithRefresh function
export const fetchWithRefresh = async (url, options = {}) => {
    const requestConfig = {
        url,
        ...options
    };

    try {
        // First attempt with current token
        let response = await tokenService.executeRequest(requestConfig);

        // If unauthorized and we have a refresh token, try to refresh
        if (response.status === 401) {
            const refreshToken = tokenService.getRefreshToken();
            
            if (refreshToken) {
                try {
                    response = await tokenService.handleTokenRefresh(requestConfig);
                } catch (refreshError) {
                    console.error('Token refresh failed:', refreshError);
                    // Redirect to login if refresh fails
                    tokenService.clearTokens();
                    window.location.href = '/';
                    return null;
                }
            } else {
                // No refresh token available, redirect to login
                tokenService.clearTokens();
                window.location.href = '/';
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
};

export default tokenService;