import React, {useRef, useEffect, useState} from 'react';
import './home.css';

const Home = () => {
    return (
        <div className="home-container">
            {/* Logo in upper left corner */}
            <img src="/logo-icon.png" alt="DigitalOC Icon" className="logo-icon" />
            
            {/* Main content */}
            <div className="content-wrapper">
                <h1 className="title">
                    <span className="title-digital">DIGITAL</span>
                    <span className="title-oc">OC</span>
                </h1>
                
                <p className="subtitle">Revolutionizing NFL playcalling</p>
            </div>
            
            {/* Begin button */}
            <button className="begin-button" onClick={() => {
                window.location.href = '/situation';
            }}>
                BEGIN
            </button>
        </div>
    );
}

export default Home;