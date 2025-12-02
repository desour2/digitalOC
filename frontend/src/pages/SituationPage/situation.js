import React, {useRef, useEffect, useState} from 'react';
import TeamDropdownMenu from '../../components/team_dropdown';

const Situation = () => {
    
    // Team attributes
    const [offenseTeam, setOffenseTeam] = useState("");
    const [defenseTeam, setDefenseTeam] = useState("");

    // Down and distance attributes
    const [down, setDown] = useState("");
    const [ydsToGo, setYdsToGo] = useState();
    const [ownOppMidfield, setOwnOppMidfield] = useState(""); // Defines whether the offense is in their own or opponent's territory or midfield
    const [ydLine50, setYdLine50] = useState(); // Yard line relative to own/opp territory (ignored if midfield selected)

    // Score attributes
    const [offensePoints, setOffensePoints] = useState(); 
    const [defensePoints, setDefensePoints] = useState();

    // Time attributes
    /* If OT is selected for quarter, the qtr/half/game seconds will be calculated as if it was the 4th quarter */
    const [quarter, setQuarter] = useState(""); 
    const [minutes, setMinutes] = useState(); 
    const [seconds, setSeconds] = useState(); 

    // Timeout attributes
    const [offenseTimeouts, setOffenseTimeouts] = useState(""); 
    const [defenseTimeouts, setDefenseTimeouts] = useState(""); 
    
    async function calculateQtrSeconds(minutes, seconds) {
        seconds = parseInt(seconds);
        minutes = parseInt(minutes);

        return seconds + (minutes * 60); 
    }

    async function calculateHalfSeconds(qtr, minutes, seconds) {
        seconds = parseInt(seconds);
        minutes = parseInt(minutes);

        if (qtr === '1' || qtr === '3') seconds += 900; 
        return seconds + (minutes * 60); 
    }

    async function calculateGameSeconds(qtr, minutes, seconds) {
        seconds = parseInt(seconds);
        minutes = parseInt(minutes);

        if (qtr === '3') seconds += 900; 
        else if (qtr === '2') seconds += 1800; 
        else if (qtr === '1') seconds += 2700; 
        return seconds + (minutes * 60); 
    }

    async function submitSituation() {
        // Ensure no required fields are left blank
        if (!offenseTeam || !defenseTeam || !down || !ydsToGo || !ownOppMidfield || (ownOppMidfield !== 'midfield' && !ydLine50) || !offensePoints || !defensePoints || !quarter || !minutes || !seconds || !offenseTimeouts || !defenseTimeouts) {
            alert("Please fill out all required fields before submitting the situation.");
            return;
        }

        if (offenseTeam === defenseTeam) {
            alert("Please select different teams for the offense and defense."); 
            return; 
        }

        // Log the situation to the console
        console.log("Sitaution submitted, here is the following situation: "); 
        console.log(`Teams (offense vs. defense) are ${offenseTeam} vs. ${defenseTeam}`); 
        console.log(`${down}${down === '1' ? 'st' : down === '2' ? 'nd' : down === '3' ? 'rd' : 'th'} & ${ydsToGo} from ${ownOppMidfield} ${ownOppMidfield !== 'midfield' ? ydLine50 : ''}`);
        console.log(`Score (offense - defense) is ${offensePoints} - ${defensePoints}`);
        console.log(`Timestamp: ${quarter}${quarter === '1' ? 'st' : quarter === '2' ? 'nd' : quarter === '3' ? 'rd' : quarter === '4' ? 'th' : ''} at ${minutes}:${seconds}`);
        console.log(`Timeouts remaining: Offense ${offenseTimeouts}, Defense ${defenseTimeouts}`);
        
        // Calculate necessary values for the situation array as needed by the backend model
        const ydLine100 = (ownOppMidfield === "own" ? 100 - parseInt(ydLine50) : ownOppMidfield === "midfield" ? 50 : ownOppMidfield === "opp" ? parseInt(ydLine50) : undefined);
        const goalToGo = (ydLine100 === parseInt(ydsToGo) ? 1 : 0);
        const scoreDiff = parseInt(offensePoints) - parseInt(defensePoints);
        const qtrSeconds = await calculateQtrSeconds(minutes, seconds);
        const halfSeconds = await calculateHalfSeconds(quarter, minutes, seconds);
        const gameSeconds = await calculateGameSeconds(quarter, minutes, seconds);

        // Situation array that will be used to call the backend and PBP model
        const situationArray = `${down}, ${ydsToGo}, ${ydLine100}, ${goalToGo}, ${qtrSeconds}, ${halfSeconds}, ${gameSeconds}, ${scoreDiff}, ${offenseTimeouts}, ${defenseTimeouts}, ${offenseTeam}, ${defenseTeam}`;
        console.log(`Situation Array: ${situationArray}`);

        // Will eventually build a fetch call here

        return; 
    }   

    return (
        <div>
            {/* ---- Header Section ---- */}
            <div style={{ paddingLeft: "20px", paddingTop: "20px" }}>
                <h1>DigitalOC</h1>
                <h4>
                    An app that uses play-by-play data and team playcalling tendencies to train an ML model 
                    that suggests the most optimal offensive play in any NFL game situation.
                </h4>
            </div>

            <br />

            {/* ---- Team Input Section ---- */}
            <div style={{ paddingLeft: "60px", paddingTop: "20px" }}>
                <h2>Teams</h2>
                
                <div style={{ paddingLeft: '20px' }}>
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Offense:</span>
                    <TeamDropdownMenu 
                        onChange={(value) => setOffenseTeam(value)}
                    /> 
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Defense:</span>
                    <TeamDropdownMenu 
                        onChange={(value) => setDefenseTeam(value)}
                    />
                </div>
            </div>

            {/* ---- Down and Distance Section ---- */}
            <div style={{ paddingLeft: "60px", paddingTop: "20px" }}>
                <h2>Down & Distance</h2>

                <div style={{ paddingLeft: '20px' }}>
                    {/* Down Selector */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Down:</span>
                    <select
                        name="down"
                        id="down"
                        style={{
                            marginLeft: '5px',
                            padding: '5px',
                            fontSize: '16px',
                        }}
                        value={down}
                        onChange={(e) => setDown(e.target.value)}
                    >
                        <option value="">-</option>
                        <option value="1">1st</option>
                        <option value="2">2nd</option>
                        <option value="3">3rd</option>
                        <option value="4">4th</option>
                    </select>

                    {/* Yards to Go */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Yards to go:</span>
                    <input
                        type="number"
                        name="ydsToGo"
                        id="ydsToGo"
                        min="1"
                        max="99"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '80px',
                        }}
                        value={ydsToGo}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if ((value >= 1 && value <= 99) || e.target.value === '') {
                                setYdsToGo(e.target.value);
                            }
                        }}
                    />

                    {/* Territory */ }
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Territory:</span>
                    <select
                        name="ownOppMidfield"
                        id="ownOppMidfield"
                        style={{
                            marginLeft: '5px',
                            padding: '5px',
                            fontSize: '16px',
                        }}
                        value={ownOppMidfield}
                        onChange={(e) => setOwnOppMidfield(e.target.value)}
                    >
                        <option value="" style={{ color: "gray" }}>-</option>
                        <option value="own">{offenseTeam !== '' ? `${offenseTeam} (OWN)` : 'OWN'}</option>
                        <option value="opp">{defenseTeam !== '' ? `${defenseTeam} (OPP)` : 'OPP'}</option>
                        <option value="midfield">MIDFIELD (50)</option>
                    </select>

                    {/* Yard line */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Yard Line (leave blank if territory is midfield):</span>
                    <input
                        type="number"
                        name="ydLine50"
                        id="ydLine50"
                        min="1"
                        max="49"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px',
                        }}
                        value={ydLine50}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if ((value >= 1 && value <= 49) || e.target.value === '') {
                                setYdLine50(e.target.value);
                            }
                        }}
                    />
                </div>
            </div>

            {/* ---- Score Section ---- */}
            <div style={{ paddingLeft: "60px", paddingTop: "20px" }}>
                <h2>Score</h2>

                <div style={{ paddingLeft: '20px' }}>
                    {/* Offense Score */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>{offenseTeam !== '' ? offenseTeam : 'Offense'} Points:</span>
                    <input
                        type="number"
                        name="offensePoints"
                        id="offensePoints"
                        min="0"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '150px',
                        }}
                        value={offensePoints}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if ((value >= 0 && value <= 99) || e.target.value === '') {
                                setOffensePoints(e.target.value);
                            }
                        }}
                    />

                    {/* Defense Score */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>{defenseTeam !== '' ? defenseTeam : 'Defense'} Points:</span>
                    <input
                        type="number"
                        name="defensePoints"
                        id="defensePoints"
                        min="0"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '150px',
                        }}
                        value={defensePoints}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if ((value >= 0 && value <= 99) || e.target.value === '') {
                                setDefensePoints(e.target.value);
                            }
                        }}
                    />
                </div>
            </div>

            {/* ---- Time Section ---- */}
            <div style={{ paddingLeft: '60px', paddingTop: '20px' }}>
                <h2>Time</h2>

                <div style={{ paddingLeft: '20px' }}>
                    {/* Quarter Selector */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Quarter:</span>
                    <select
                        name="quarter"
                        id="quarter"
                        style={{
                            marginLeft: '5px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px'
                        }}
                        value={quarter}
                        onChange={(e) => {
                            setQuarter(e.target.value);
                        }}
                    >
                        <option value="">-</option>
                        <option value="1">1st</option>
                        <option value="2">2nd</option>
                        <option value="3">3rd</option>
                        <option value="4">4th</option>
                        <option value="OT">OT</option>
                    </select>

                    {/* Minutes */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Minutes:</span>
                    <input
                        type="number"
                        name="minutes"
                        id="minutes"
                        min="0"
                        max="15"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px',
                        }}
                        value={minutes}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if ((value >= 0 && value <= 15) || e.target.value === '') {
                                setMinutes(e.target.value);
                                // If minutes is set to 15, automatically set seconds to 0
                                if (value === 15) {
                                    setSeconds(0);
                                }
                            }
                        }}
                    />

                    {/* Seconds */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>Seconds:</span>
                    <input
                        type="number"
                        name="seconds"
                        id="seconds"
                        min="0"
                        max="59"
                        style={{
                            marginLeft: '10px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px',
                        }}
                        value={seconds}
                        onChange={(e) => {
                            const value = parseInt(e.target.value);
                            // If minutes is 15, only allow seconds to be 0
                            if (parseInt(minutes) === 15) {
                                setSeconds(0);
                                return;
                            }
                            // Normal validation for other cases
                            if ((value >= 0 && value <= 59) || e.target.value === '') {
                                setSeconds(e.target.value);
                            }
                        }}
                    />
                </div>
            </div>

            {/* ---- Timeouts Section ---- */}
            <div style={{ paddingLeft: '60px', paddingTop: '20px' }}>
                <h2>Timeouts</h2>

                <div style={{ paddingLeft: '20px' }}>
                    {/* Offense Timeouts */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>{offenseTeam !== '' ? offenseTeam : 'Offense'} Timeouts:</span>
                    <select
                        name="offenseTimeouts"
                        id="offenseTimeouts"
                        style={{
                            marginLeft: '5px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px'
                        }}
                        value={offenseTimeouts}
                        onChange={(e) => setOffenseTimeouts(e.target.value)}
                    >
                        <option value="">-</option>
                        <option value="0">0</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                    </select>

                    {/* Defense Timeouts */}
                    <span style={{ paddingLeft: '40px', paddingRight: '5px' }}>{defenseTeam !== '' ? defenseTeam : 'Defense'} Timeouts:</span>
                    <select
                        name="defenseTimeouts"
                        id="defenseTimeouts"
                        style={{
                            marginLeft: '5px',
                            padding: '5px',
                            fontSize: '16px',
                            width: '100px'
                        }}
                        value={defenseTimeouts}
                        onChange={(e) => setDefenseTimeouts(e.target.value)}
                    >
                        <option value="">-</option>
                        <option value="0">0</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                    </select>
                </div>
            </div>

            {/* ---- Submit Button ---- */}
            <div style={{ paddingLeft: "60px", paddingTop: "60px" }}>
                <button
                    type="submit"
                    style={{
                        padding: "10px 100px",
                        fontSize: "16px",
                        backgroundColor: "#12dab9ff",
                        color: "black",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                    onClick={submitSituation}
                >
                    Submit
                </button>
            </div>

            <br />
            <br />
            <br />
            <br />
            <br />
            <br />
            <br />

        </div>
    );
}

export default Situation;