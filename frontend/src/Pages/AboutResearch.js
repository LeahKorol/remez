import React from "react";
import { useNavigate } from "react-router-dom";
import './App.css';

function AboutResearch() {
    const navigate = useNavigate();

    return (
        <div className="App">
            <nav className="navbar">
                <div className="logo" onClick={() => navigate('/')}>REMEZ</div>
            </nav>

            <div className="content">
                <h1 className="main-title">About the Research</h1>

                <p className="description" style={{ maxWidth: '700px' }}>
                    REMEZ is built on evidence-based research conducted by Dr. Boris Gorelik to provide reliable
                    medication interaction analysis. Our team, Eng. Leah Korol and Eng. Talya Kazayof developed this
                    website based on his validated research and methodology.
                </p>

                <p className="description" style={{ maxWidth: '700px', marginTop: '20px' }}>
                    You can access Dr. Boris Gorelik's main research paper here:
                    <a href="https://gorelik.net/2020/03/11/the-cardiovascular-safety-of-antiobesity-drugs-analysis-of-signals-in-the-fda-adverse-event-report-system-database"
                        target="_blank" rel="noopener noreferrer"
                        style={{ color: '#5e68f1', textDecoration: 'underline', marginLeft: '5px' }}>
                        View Research
                    </a>
                </p>
            </div>

            <div className="footer">
                <p>Created by Eng. Leah Korol and Eng. Talya Kazayof</p>
                <p>In collaboration with Dr. Boris Gorelik</p>
            </div>
        </div>
    );
}

export default AboutResearch;
