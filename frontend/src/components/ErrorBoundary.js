import React from "react";
import "./ErrorBoundary.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("❌ REMEZ frontend crashed:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-container">
          <div className="error-card">
            <div className="error-logo">REMEZ</div>

            <h1 className="error-title">Something went wrong 😞</h1>
            <p className="error-message">
              We encountered an unexpected issue. Please refresh the page or try again later.
            </p>

            <button className="reload-button" onClick={this.handleReload}>
              Reload Page
            </button>

            <p className="error-note">
              If the problem persists, contact the support team or check your internet connection.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;