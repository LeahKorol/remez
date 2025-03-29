import React from "react";
import { useNavigate } from "react-router-dom";
import './App.css'

function Home() {
    const navigate = useNavigate();

    const handleLoginClick = () => {
        navigate('/login');
    };

    return (
        <div className="App">
            <nav className="navbar">
                <div className="logo">REMEZ</div>
                <button className="login-btn" onClick={handleLoginClick}>Login</button>
            </nav>

            <div className="content">
                <div className="welcome-banner">Welcome to REMEZ</div>

                <h1 className="main-title">
                    Advanced Medication Interaction Analysis
                </h1>

                <p className="description">
                    Discover potential interactions between medications and their side effects using our
                    sophisticated analysis tools.
                </p>

                <div className="features-container">
                    <div className="feature-card">
                        <div className="icon-circle purple">
                            <span className="icon">☷</span>
                        </div>
                        <h3 className="feature-title">Advanced Analysis</h3>
                        <p className="feature-description">
                            Precise medication interaction evaluation using modern algorithms
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-circle blue">
                            <span className="icon">⦿</span>
                        </div>
                        <h3 className="feature-title">Evidence-Based</h3>
                        <p className="feature-description">
                            Research-backed data analysis for reliable results
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-circle blue-light">
                            <span className="icon">⚡</span>
                        </div>
                        <h3 className="feature-title">Real-Time Results</h3>
                        <p className="feature-description">
                            Instant visualization of interaction analysis
                        </p>
                    </div>
                </div>

                <button className="begin-btn" onClick={handleLoginClick}>Login to Begin</button>

                <div className="footer">
                    <p>Created by Eng. Leah Korol and Eng. Talya Kazayof</p>
                    <p>In collaboration with Dr. Boris Gorelik</p>
                </div>
            </div>
        </div>
    );
}

export default Home;