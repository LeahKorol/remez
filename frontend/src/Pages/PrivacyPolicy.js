import React from "react";
import { useNavigate } from "react-router-dom";
import './App.css';

function PrivacyPolicy() {
    const navigate = useNavigate();

    return (
        <div className="App">
            <nav className="navbar">
                <div className="logo" onClick={() => navigate('/')}>REMEZ</div>
            </nav>

            <div className="content">
                <h1 className="main-title">Privacy & Copyright Policy</h1>

                <p className="description" style={{ maxWidth: '700px' }}>
                    All content, design, software, and materials on this website are the intellectual property of REMEZ
                    and its creators. No part of this site may be copied, reproduced, or distributed in any form without 
                    the express written permission of the authors.
                </p>

                <p className="description" style={{ maxWidth: '700px', marginTop: '20px' }}>
                    Unauthorized use or reproduction of any materials is strictly prohibited. By using this website, 
                    you agree to comply with these terms.
                </p>
            </div>

            <div className="footer">
                <p>Created by Eng. Leah Korol and Eng. Talya Kazayof</p>
                <p>In collaboration with Dr. Boris Gorelik</p>
            </div>
        </div>
    );
}

export default PrivacyPolicy;
