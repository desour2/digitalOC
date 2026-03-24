from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask
import matplotlib.pyplot as plt

from model_trainers.pbp_situation_model import predict_play
from model_trainers.run_model import predict_run_metrics
from model_trainers.pass_model import predict_pass_metrics
from model_trainers.exp_run_yards_model import predict_exp_yards_run
from model_trainers.exp_pass_yards_model import predict_exp_yards_pass
from routeDrawer.playDraw import visualize_play

import joblib
from pathlib import Path

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})


# Load the PBP, run and pass models when the application starts
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)
pbp_model = joblib.load(model_dir / "pbp_situation_model.joblib")
run_models = joblib.load(model_dir / "run_models.joblib")
pass_models = joblib.load(model_dir / "pass_models.joblib")

import json
with open(model_dir / "pbp_situation_model_meta.json", 'r') as f:
    metadata = json.load(f)
pbp_feature_columns = metadata["feature_columns"]


@app.route("/suggestPlay", methods=['POST'])
def suggest_play():
    ''' Endpoint from the React frontend to get play suggestion based on the incoming situation and history '''
    
    # Extract the JSON payload sent by React
    data = request.get_json()
    current_situation = data.get('current_situation', {})
    play_history = data.get('play_history', []) # Array of previous plays in this drive
    
    # Extract base features
    yardline = current_situation.get('yardline_100', 50)
    score_diff = current_situation.get('score_differential', 0)
    
    if abs(score_diff) > 16:
        print("NOTICE: Game state is non-competitive. Suggestion may be biased by clock-management.")

    is_midfield_aggression = 1 if 35 <= yardline <= 45 else 0
    is_deep_redzone = 1 if yardline <= 10 else 0

    # Calculate sequence features dynamically from the play_history array
    prev_is_pass = 0
    prev_is_run = 0
    prev_yards_gained = 0
    two_consecutive_runs = 0
    two_consecutive_passes = 0
    
    if len(play_history) > 0:
        last_play = play_history[-1]
        prev_is_pass = 1 if last_play.get('play_type') == 'pass' else 0
        prev_is_run = 1 if last_play.get('play_type') == 'run' else 0
        prev_yards_gained = last_play.get('yards_gained', 0)
        
    if len(play_history) >= 2:
        two_plays_ago = play_history[-2]
        if last_play.get('play_type') == 'run' and two_plays_ago.get('play_type') == 'run':
            two_consecutive_runs = 1
        if last_play.get('play_type') == 'pass' and two_plays_ago.get('play_type') == 'pass':
            two_consecutive_passes = 1

    # Build the final situation array in the exact order the prediction functions expect
    situation = [
        current_situation.get('down', 1),
        current_situation.get('ydstogo', 10),
        yardline,
        current_situation.get('goal_to_go', 0),
        current_situation.get('quarter_seconds_remaining', 900),
        current_situation.get('half_seconds_remaining', 1800),
        current_situation.get('game_seconds_remaining', 3600),
        score_diff,
        current_situation.get('posteam_timeouts_remaining', 3),
        current_situation.get('defteam_timeouts_remaining', 3),
        current_situation.get('posteam', 'UNK'),
        current_situation.get('defteam', 'UNK'),
        is_midfield_aggression,
        is_deep_redzone,
        # --- NEW SEQUENCE FEATURES ---
        prev_is_pass,
        prev_is_run,
        prev_yards_gained,
        two_consecutive_runs,
        two_consecutive_passes,
        current_situation.get('defense_coverage_type', 'UNKNOWN')
    ]

    # Predict whether the play type should be a run or pass
    prediction_int, confidence = predict_play(situation, trained_model=pbp_model, feature_columns=pbp_feature_columns)

    # 1 = Pass Intent (Passes, Sacks, Scrambles), 0 = Run Intent
    prediction = 'pass' if prediction_int == 1 else 'run'
    
    exp_yards = None

    # Depending on the prediction, feed it into the run or pass model
    if prediction == 'run':
        run_prediction = predict_run_metrics(situation, trained_models=run_models)
        run_gap = run_prediction['run_gap']
        run_location = run_prediction['run_location']
        offense_formation = run_prediction['offense_formation']
        personnel_off = run_prediction['personnel_off']

        # Modify the offense personnel to get only the RBs, WRs, and TEs when visualizing the play
        personnel_rb_wr_te = ', '.join([part for part in personnel_off.split(', ') if any(pos in part for pos in ['RB', 'WR', 'TE'])])

        run_play_input = {
            "yardline_100": yardline,
            "down": situation[0],
            "ydstogo": situation[1],
            "pass_length": None,
            "pass_location": None, 
            "air_yards": None, 
            "run_location": run_location,
            "run_gap": run_gap,
            "rusher": 'N/A', 
            "receiver": None, 
            "offense_formation": offense_formation,
            "offense_personnel": personnel_rb_wr_te,
            "route": None,
            "involved_player_position": "RB",
            "posteam": situation[10],
            "defteam": situation[11]
        }

        visualize_play(run_play_input)
        exp_yards = str(predict_exp_yards_run(run_play_input).round(2))

    elif prediction == 'pass':
        pass_prediction = predict_pass_metrics(situation, trained_models=pass_models)
        pass_length = pass_prediction['pass_length']
        pass_location = pass_prediction['pass_location']
        offense_formation = pass_prediction['offense_formation']
        offense_personnel = pass_prediction['offense_personnel']
        route = pass_prediction['route']
        receiver_position = pass_prediction['receiver_position']

        pass_play_input = {
            "yardline_100": yardline,
            "down": situation[0],
            "ydstogo": situation[1],
            "pass_length": pass_length,
            "pass_location": pass_location,
            "air_yards": 10, # Placeholder value    
            "run_location": None,
            "run_gap": None,
            "rusher": None,
            "receiver": 'N/A',
            "offense_formation": offense_formation,
            "offense_personnel": offense_personnel,
            "route": route,
            "involved_player_position": receiver_position,
            "posteam": situation[10],
            "defteam": situation[11]
        }

        visualize_play(pass_play_input)
        p_complete_and_exp_yards = predict_exp_yards_pass(pass_play_input)
        exp_yards = f"{p_complete_and_exp_yards[0].round(2)}\n% will be complete: {(p_complete_and_exp_yards[1]*100).round(0)}"

    return jsonify({"expected_yards": exp_yards})

@app.route("/", methods=['GET'])
def home():
    return "<h1>Server is working</h1><p>"

@app.route("/playVisualization", methods=['GET'])
def get_play_visualization():
    return send_file('play_visualization.png', mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')