import React, {useEffect, useState} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './result.css';

const Result = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const situationData = location.state;
    const [visualizationImage, setVisualizationImage] = useState(null);

    useEffect(() => {
        console.log("Received situation data:", situationData);

        // Fetch the play visualization image from the Flask backend
        fetch('http://localhost:5000/playVisualization', { method: 'GET' })
            .then(response => response.blob())
            .then(imageBlob => {
                // Create a local URL of the image blob and set it as the visualization image source
                const imageObjectURL = URL.createObjectURL(imageBlob);
                setVisualizationImage(imageObjectURL);
            })
            .catch(error => {
                console.error("Error fetching play visualization:", error);
            });

    }, [situationData]);


    if (!situationData) {
        return (
            <div className="result-container">
                <h1>No situation data available</h1>
                <button onClick={() => navigate('/situation')}>Go to Situation Page</button>
            </div>
        );
    }

    return (
        <div className="result-container">
            <h1 className="result-title">SITUATION RESULT</h1>
            
            <div className="result-content">
                <h2>Raw Situation Array:</h2>
                <pre className="situation-output">{situationData.situationArray}</pre>
                
                <h2>Situation Details:</h2>
                <div className="details-grid">
                    <div className="detail-item">
                        <span className="detail-label">Offense:</span>
                        <span className="detail-value">{situationData.offenseTeam}</span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Defense:</span>
                        <span className="detail-value">{situationData.defenseTeam}</span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Down & Distance:</span>
                        <span className="detail-value">{situationData.down} & {situationData.ydsToGo}</span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Field Position:</span>
                        <span className="detail-value">
                            {situationData.ownOppMidfield === 'midfield' ? 'Midfield' : `${situationData.ownOppMidfield.toUpperCase()} ${situationData.ydLine50}`}
                        </span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Score:</span>
                        <span className="detail-value">{situationData.offensePoints} - {situationData.defensePoints}</span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Time:</span>
                        <span className="detail-value">Q{situationData.quarter} - {situationData.minutes}:{String(situationData.seconds).padStart(2, '0')}</span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">Timeouts:</span>
                        <span className="detail-value">OFF: {situationData.offenseTimeouts}, DEF: {situationData.defenseTimeouts}</span>
                    </div>
                </div>

                <h2>Play Visualization:</h2>
                <div className="visualization-container">
                    <img src={visualizationImage} alt="Play Visualization" className="visualization-image" />
                </div>
            </div>

            <button className="back-button" onClick={() => navigate('/situation')}>
                Back to Situation
            </button>
        </div>
    );
};

export default Result;
