import pandas as pd
import subprocess
import os
import io

data = {
    "receive_2h_ko": [0],
    "home_team": ["SEA"],
    "posteam": ["SEA"],
    "score_differential": [0],
    "half_seconds_remaining": [1800],
    "game_seconds_remaining": [3600],
    "spread_line": [1],
    "down": [1], 
    "ydstogo": [10],
    "yardline_100": [75],
    "posteam_timeouts_remaining": [3],
    "defteam_timeouts_remaining": [3]
}
py_df = pd.DataFrame(data)

r_script_path = "calculate_wp.R"
temp_csv_file= "temp_input.csv"


try:
    # --- 2. Save the DataFrame to a temporary CSV ---
    py_df.to_csv(temp_csv_file, index=False)
    
    # --- 3. Run the R script using subprocess ---
    # This assumes 'Rscript' is in your system's PATH
    # We pass the R script and the temp file as arguments
    command = ["Rscript", r_script_path, temp_csv_file]

    # capture_output=True gets stdout/stderr
    # text=True decodes them as strings (not bytes)
    # check=True raises an error if the R script fails
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    # --- 4. Read the captured output back into pandas ---
    # result.stdout contains the CSV string printed by the R script
    # We use io.StringIO to treat the string as a file
    csv_output_string = result.stdout
    final_wp_df = pd.read_csv(io.StringIO(csv_output_string))

    # --- 5. Show the final result ---
    print("Successfully got win probabilities from R:")
    print(final_wp_df)

except subprocess.CalledProcessError as e:
    print("Error running R script:")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
except FileNotFoundError:
    print("Error: 'Rscript' command not found.")
    print("Please ensure R is installed and 'Rscript' is in your system PATH.")
finally:
    # --- 6. Clean up the temporary file ---
    if os.path.exists(temp_csv_file):
        os.remove(temp_csv_file)