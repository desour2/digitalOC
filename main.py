''' 
    Test cases only
'''

from pbp_situation_model import train_pbp_model, predict_play
from run_model import train_run_models, predict_run_metrics


if __name__ == "__main__":
    # Test situations to predict play type - [down, ydstogo, yardline_100, goal_to_go, quarter_seconds_remaining, half_seconds_remaining, game_seconds_remaining, score_differential, posteam_timeouts_remaining, defteam_timeouts_remaining, posteam, defteam]
    test_case_1 = [2, 5, 30, 0, 720, 720, 2520, 0, 3, 3, 'KC', 'BUF'] # 2nd & 5 from opponent's 30-yard line, Q2-12:00, tied game, balanced situation
    # test_case_2 = [3, 8, 50, 0, 180, 1080, 1080, -3, 2, 3, 'GB', 'DAL'] # 3rd & 8 from midfield, Q3-3:00, down by 3, passing situation
    # test_case_3 = [1, 10, 75, 0, 480, 1380, 3180, 7, 3, 3, 'SF', 'SEA'] # 1st & 10 from own 25-yard line, Q1-8:00, ahead by 7, balanced situation
    # test_case_4 = [1, 8, 8, 1, 95, 95, 95, -4, 1, 2, 'NE', 'NYG'] # 1st & Goal from 8-yard line, Q4-1:35, down by 4, red zone situation  
    # test_case_5 = [4, 2, 35, 0, 45, 45, 45, -6, 0, 1, 'TB', 'DET'] # 4th & 2 from opponent's 35, Q4-0:45, down by 6, desperation situation
    # test_case_6 = [3, 1, 60, 0, 600, 1500, 3300, 0, 2, 2, 'MIA', 'NYJ'] # 3rd & 1 from own 40, Q1-10:00, tied game, short yardage situation
    # test_case_7 = [1, 1, 1, 1, 600, 600, 2400, 0, 2, 2, 'PHI', 'LAR'] # 1st & Goal from the 1, Q3-10:00, Tush Push Situation for the Eagles 
    # test_case_8 = [3, 15, 80, 0, 900, 900, 900, -10, 1, 2, 'CIN', 'PIT'] # 3rd and long from own 20, Q4-15:00, down by 10, passing situation

    # all_test_cases = [test_case_1, test_case_2, test_case_3, test_case_4, test_case_5, test_case_6, test_case_7, test_case_8]

    all_test_cases = [test_case_1]


    ''' Predict whether the play for the given situation should be a run or pass '''

    # Train the PBP Situation Model
    trained_model, feature_columns = train_pbp_model()
    print(feature_columns)
    print()

    # Train the Run Models 
    all_run_models = train_run_models()

    for test_case in all_test_cases:
        # Predict the most optimal play for each situation
        prediction, confidence = predict_play(test_case, trained_model, feature_columns)

        ''' 
            From this point on, depending on the predicition, you would either feed it into the run or pass model. 

            Just like the PBP model, build the run/pass models in separate files and then import them here.
        '''

        if prediction == 'run':
            run_prediction = predict_run_metrics(test_case, all_run_models)

            print(f"Run Prediction: {run_prediction}")


        
    