# DigitalOC

An intelligent NFL play-calling assistant that leverages machine learning and real play-by-play data to recommend optimal offensive plays for any game situation.

## Overview

DigitalOC is a full-stack web application that combines NFL play-by-play data, team Elo ratings, and Next Gen Stats to power ML models that predict the best offensive strategy. The app features an interactive React frontend where users can input game situations and receive AI-driven play recommendations with visual play diagrams.

## Features

- **Interactive Situation Input**: Modern UI with team selection, down/distance, field position, score, time, and timeout tracking
- **Dynamic Team Branding**: Real-time gradient backgrounds using official NFL team colors
- **ML-Powered Predictions**: 
  - Play type classification (run vs. pass)
  - Run play metrics prediction (EPA, success rate, yards gained)
  - Pass play metrics prediction (completion probability, air yards, YAC)
- **Visual Play Diagrams**: Automated route visualization with receiver positions and routes
- **Real-Time Results**: Side-by-side comparison of situation details and recommended plays

## Tech Stack

### Frontend
- **React 19.2** with React Router for navigation
- **Custom CSS** with gradient animations and team-specific theming
- **Orbitron font** for a modern, futuristic aesthetic
- Dynamic form validation and interactive UI components

### Backend
- **Flask** API with CORS support
- **scikit-learn** for ML models (Random Forest, Logistic Regression, Linear Regression)
- **pandas** for data processing and feature engineering
- **matplotlib** for play visualization generation
- Team Elo rating system for performance-based predictions

### Data Sources
- NFL play-by-play data (2020-2024 seasons)
- Next Gen Stats (passing, receiving, rushing metrics)
- Snap counts and participation data
- Custom team Elo ratings

## Project Structure

```
digitalOC/
├── frontend/                 # React application
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage/    # Landing page
│   │   │   ├── SituationPage/  # Game situation input
│   │   │   └── ResultPage/  # Play recommendations & visualization
│   │   └── logos/           # NFL team logos (32 teams)
└── backend/                 # Flask API and ML models
    ├── app.py                   # Flask API server
    ├── pbp_situation_model.py   # Play type classification model
    ├── run_model.py             # Run play metrics prediction
    ├── pass_model.py            # Pass play metrics prediction
    ├── TeamElo.py               # Team Elo rating system
    ├── routeDrawer/             # Play visualization module
    ├── data/                    # NFL datasets (PBP, Next Gen Stats)
    └── models/                  # Trained model artifacts
```

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Model Training

- ⚠️ Important: The trained model artifacts are not included in the repository due to size constraints. You will need to run the training scripts to generate the models before starting the backend server.

-  Run the training scripts for each model:
```bash
cd backend
python pbp_situation_model.py
python run_model.py
python pass_model.py
```
-  Trained model artifacts will be saved in the `backend/models/` directory.

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/nworobec/digitalOC.git
cd digitalOC
```

2. Install Python dependencies:
```bash
pip install flask flask-cors pandas scikit-learn matplotlib numpy
```

3. Navigate to backend directory:
```bash
cd backend
```

4. Start the Flask server:
```bash
python app.py
```
The API will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```
The app will open at `http://localhost:3000`

## 📊 Models & Data Processing

### Play-by-Play Situation Model
- **Input Features**: Down, yards to go, field position, score differential, time remaining, timeouts, team Elo
- **Output**: Play type recommendation (run/pass)
- **Algorithm**: Random Forest Classifier
- **Training Data**: 2024 NFL season play-by-play data

### Run Model
Predicts expected metrics for run plays:
- Expected Points Added (EPA)
- Success rate
- Yards gained

### Pass Model
Predicts expected metrics for pass plays:
- Completion probability
- Air yards
- Yards after catch (YAC)

### Team Elo System
Custom Elo ratings categorized by play situation (e.g., early down, late & long, goal line) to capture team strength in different scenarios.

## Contributors
**Noah Worobec** ([@nworobec](https://github.com/nworobec)),
**Russel C** ([@russelchao](https://github.com/russellchao)),
**Gavin C** ([@gavinc1225](https://github.com/gavinc1225)),
**Nicole S** ([@nstepanenko464](https://github.com/nstepanenko464)),
**Daniel M** ([@DanKMM](https://github.com/DanKMM)),
**Olakiite F** ([@fatuko](https://github.com/fatuko)),
**Rondalph T** ([legffy](https://github.com/legffy)),
**Rafiki M** ([@RafikiMwethuku](https://github.com/RafikiMwethuku))


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Links

- [NFL Play-by-Play Data](https://github.com/nflverse/nflverse-data)
- [Next Gen Stats](https://nextgenstats.nfl.com/)

## Future Enhancements

- Personnel grouping recommendations
- Historical success rate comparisons
- Real-time game integration
- Advanced route tree customization
- Defensive formation predictions
- Multi-season model training
