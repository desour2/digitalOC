Russell, Rafiki, Noah, Nicole

Each play must have:
individual play ID (need to be in dataframe, not for input for model)
Game ID (need to be in dataframe, not for input for model)
type of play (run/pass) (for output for model)
possession/defense team (input for model)
Yard line (input for model)
Timeouts remaining for each team (input for model)
Yards to go for first down (input for model)
Successful play? (output for model)
Score differential (input for model)

Inputs for model:
Down (down)
Distance (ydstogo)
Time (quarter_seconds_remaining, half_seconds_remaining, game_seconds_remaining)
Quarter (qtr)
Yard line
Difference of score between posteam and defteam (score_differential) -> (- if losing, + if winning)
Possessing team (posteam)
Defending team (defteam)
Timeouts remaining (posteam_timeouts_remaining)

Necessary functions:
Load raw data
Filter (only include run and pass plays for new dataframe)
Label (include run direction + gap, pass distance + direction)
Features (input for model, all situation stuff)
Preprocess (calling previous functions, creating complete dataframe for model)
Model

How we can split the work to train the model:
Add pass data
Write cleaning function for rows with ‘NaN’ ✅


Determine if a pass play was successful 
