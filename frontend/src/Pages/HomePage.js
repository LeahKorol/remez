import React, {useState} from "react";
import { useNavigate } from "react-router-dom";
import TutorialCarousel from "../components/TutorialCarousel";
import './App.css'


function Home() {
    const navigate = useNavigate();

    const [showTutorial, setShowTutorial] = useState(false);

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
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="lucide lucide-beaker w-6 h-6 text-purple-600"
                                data-lov-id="src/client/pages/Index.tsx:29:16"
                                data-lov-name="BeakerIcon"
                                data-component-path="src/client/pages/Index.tsx"
                                data-component-line="29"
                                data-component-file="Index.tsx"
                                data-component-name="BeakerIcon"
                                data-component-content="%7B%22className%22%3A%22w-6%20h-6%20text-purple-600%22%7D">
                                <path d="M4.5 3h15"></path><path d="M6 3v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V3"></path>
                                <path d="M6 14h12"></path>
                            </svg>
                        </div>
                        <h3 className="feature-title">Advanced Analysis</h3>
                        <p className="feature-description">
                            Precise medication interaction evaluation using modern algorithms
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-circle blue">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="lucide lucide-shield-check w-6 h-6 text-blue-600"
                                data-lov-id="src/client/pages/Index.tsx:39:16"
                                data-lov-name="ShieldCheckIcon"
                                data-component-path="src/client/pages/Index.tsx"
                                data-component-line="39"
                                data-component-file="Index.tsx"
                                data-component-name="ShieldCheckIcon"
                                data-component-content="%7B%22className%22%3A%22w-6%20h-6%20text-blue-600%22%7D">
                                <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"></path>
                                <path d="m9 12 2 2 4-4"></path>
                            </svg>
                        </div>
                        <h3 className="feature-title">Evidence-Based</h3>
                        <p className="feature-description">
                            Research-backed data analysis for reliable results
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-circle blue-light">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="lucide lucide-activity w-6 h-6 text-indigo-600"
                                data-lov-id="src/client/pages/Index.tsx:49:16"
                                data-lov-name="ActivityIcon"
                                data-component-path="src/client/pages/Index.tsx"
                                data-component-line="49"
                                data-component-file="Index.tsx"
                                data-component-name="ActivityIcon"
                                data-component-content="%7B%22className%22%3A%22w-6%20h-6%20text-indigo-600%22%7D">
                                <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"></path>
                            </svg>
                        </div>
                        <h3 className="feature-title">Real-Time Results</h3>
                        <p className="feature-description">
                            Instant visualization of interaction analysis
                        </p>
                    </div>
                </div>

                <button className="begin-btn" onClick={handleLoginClick}>Login to Begin</button>

                <button
                    className="help-button"
                    onClick={() => setShowTutorial(true)}
                    aria-label="Open tutorial"
                >
                    ?
                </button>

                <TutorialCarousel
                    open={showTutorial}
                    onClose={() => setShowTutorial(false)}
                />

                <div className="footer">
                  <p>Created by Eng. Leah Korol and Eng. Talya Kazayof</p>
                  <p>In collaboration with Dr. Boris Gorelik</p>
                  <div className="footer-links">
                    <a href="/about-research" className="footer-link">About the Research</a>
                    <span className="separator">|</span>
                    <a href="/privacy-policy" className="footer-link">Privacy Policy</a>
                  </div>
                </div>
            </div>
        </div>
    );
}

export default Home;
