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
                    REMEZ is built on evidence-based research to provide reliable medication interaction analysis. 
                    The algorithms and methodology are derived from peer-reviewed studies and validated by clinical experts.
                </p>

                <p className="description" style={{ maxWidth: '700px', marginTop: '20px' }}>
                    You can access the main research paper here: 
                    <a href="YOUR_RESEARCH_LINK_HERE" target="_blank" rel="noopener noreferrer" 
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
