import nflreadpy as nfl
import pandas as pd
import numpy as np


# calculates team passer rating and rusher rating based on nflreadpy team stats
# input team abbreviations and seasons to include


def load_team_stats(pos_team, def_team, All_seasons, seasonsList):
    if All_seasons:
        team_stats = nfl.load_team_stats(seasons=True)
    elif seasonsList and not All_seasons:
        team_stats = nfl.load_team_stats(seasons=seasonsList)

    # if want to define a range of seasons or pick certain seasons

    #team_stats = nfl.load_team_stats(seasons=[2012, 2013, 2014, 2015,2016,2017, 2018, 2019, 2020])
    team_stats_pandas = team_stats.to_pandas()
    filtered_teams = team_stats_pandas[team_stats_pandas['team'].isin([pos_team, def_team]) &
                                       team_stats_pandas['opponent_team'].isin([pos_team, def_team])]
    return filtered_teams

def calculate_offensive_pass_rating(row):
    cmp = row['completions']
    att = row['attempts']
    yds = row['passing_yards']
    td = row['passing_tds']
    interceptions = row['passing_interceptions']
    if att == 0: return 0.0

    a = max(0, min(((cmp / att) - 0.3) * 5, 2.375))
    b = max(0, min(((yds / att) - 3) * 0.25, 2.375))
    c = max(0, min((td / att) * 20, 2.375))
    d = max(0, min(2.375 - ((interceptions / att) * 25), 2.375))
    return ((a + b + c + d) / 6) * 100

def calculate_rush_rating(row):
    att = row['carries']
    yds = row['rushing_yards']
    tds = row['rushing_tds']
    fumbles = row['rushing_fumbles_lost']   
    if att == 0: return 0.0

    # Calculate Adjusted Yards
    adjusted_yards = yds + (tds * 20) - (fumbles * 25)
    
    # Calculate the rating
    # Use np.where to avoid 0/0 errors
    rating = np.where(att == 0, 0.0, (adjusted_yards / att) * 20)
    
    return rating

def get_team_pass_rating(pos_team, def_team):
    pass_rating_columns = ['completions', 'attempts', 'passing_yards', 'passing_tds', 'passing_interceptions']
    filtered_teams = load_team_stats(pos_team, def_team, All_seasons, seasonsList)
    
    pass_rating_data = filtered_teams[pass_rating_columns]
    pass_rating_df = pd.DataFrame(pass_rating_data)
    pass_rating_df['pass_rating'] = pass_rating_df.apply(calculate_offensive_pass_rating, axis=1)
    return pass_rating_df['pass_rating'].mean()

def get_team_rush_rating(pos_team, def_team):
    rush_rating_columns = ['carries', 'rushing_yards', 'rushing_tds', 'rushing_fumbles_lost']
    filtered_teams = load_team_stats(pos_team, def_team, All_seasons, seasonsList)
    
    rush_rating_data = filtered_teams[rush_rating_columns]
    rush_rating_df = pd.DataFrame(rush_rating_data)
    rush_rating_df['rush_rating'] = rush_rating_df.apply(calculate_rush_rating, axis=1)
    return rush_rating_df['rush_rating'].mean()



if __name__ == "__main__":
    pos_team = input("Enter the offensive team abbreviation (e.g., 'NE' for New England Patriots): ")
    def_team = input("Enter the defensive team abbreviation (e.g., 'NYG' for New York Giants): ")
    All_seasons = input("Do you want to include all seasons? (yes/no): ").strip().lower() == 'yes'
    if not All_seasons:
        seasons_input = input("Enter the seasons you want to include, separated by commas (e.g., '2018,2019,2020'): ")
        seasonsList = [int(season.strip()) for season in seasons_input.split(',')]


    print("PASSER RATING:", get_team_pass_rating(pos_team, def_team))
    print("RUSHER RATING:", get_team_rush_rating(pos_team, def_team))
