import React from "react";

const TeamDropdownMenu = ({ team, onChange }) => {
    return (
        <>
            <label htmlFor="team" style={{ paddingLeft: '20px' }}></label>
            <select 
                name="team" 
                id="team" 
                style={{ 
                    padding: '5px', 
                    fontSize: '16px',
                    width: '300px'
                }}
                value={team}
                onChange={(e) => onChange(e.target.value)}
            >
                <option value="" style={{ color: "gray" }}>-</option>
                <option value="ARI">Arizona Cardinals</option>
                <option value="ATL">Atlanta Falcons</option>
                <option value="BAL">Baltimore Ravens</option>
                <option value="BUF">Buffalo Bills</option>
                <option value="CAR">Carolina Panthers</option>
                <option value="CHI">Chicago Bears</option>
                <option value="CIN">Cincinnati Bengals</option>
                <option value="CLE">Cleveland Browns</option>
                <option value="DAL">Dallas Cowboys</option>
                <option value="DEN">Denver Broncos</option>
                <option value="DET">Detroit Lions</option>
                <option value="GB">Green Bay Packers</option>
                <option value="HOU">Houston Texans</option>
                <option value="IND">Indianapolis Colts</option>
                <option value="JAX">Jacksonville Jaguars</option>
                <option value="KC">Kansas City Chiefs</option>
                <option value="LV">Las Vegas Raiders</option>
                <option value="LAC">Los Angeles Chargers</option>
                <option value="LAR">Los Angeles Rams</option>
                <option value="MIA">Miami Dolphins</option>
                <option value="MIN">Minnesota Vikings</option>
                <option value="NE">New England Patriots</option>
                <option value="NO">New Orleans Saints</option>
                <option value="NYG">New York Giants</option>
                <option value="NYJ">New York Jets</option>
                <option value="PHI">Philadelphia Eagles</option>
                <option value="PIT">Pittsburgh Steelers</option>
                <option value="SF">San Francisco 49ers</option>
                <option value="SEA">Seattle Seahawks</option>
                <option value="TB">Tampa Bay Buccaneers</option>
                <option value="TEN">Tennessee Titans</option>
                <option value="WAS">Washington Commanders</option>
            </select>
        </>
    );
}; 

export default TeamDropdownMenu;