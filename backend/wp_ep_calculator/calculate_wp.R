
# Load necessary libraries
suppressPackageStartupMessages(library(nflfastR))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("No input file provided.", call. = FALSE)
}
input_filepath <- args[1]

#read the CSV file passed from Python
# specify column to avoid messags in output
data <- readr::read_csv(input_filepath, col_types = cols(
  receive_2h_ko = col_double(),
  home_team = col_character(),
  posteam = col_character(),
  score_differential = col_double(),
  half_seconds_remaining = col_double(),
  game_seconds_remaining = col_double(),
  spread_line = col_double(),
  down = col_double(),
  ydstogo = col_double(),
  yardline_100 = col_double(),
  posteam_timeouts_remaining = col_double(),
  defteam_timeouts_remaining = col_double()
))

# nflfastR win probability calculation
results <- nflfastR::calculate_win_probability(data) %>%
  dplyr::select(wp, vegas_wp)

#Print the final data to standard output
write.csv(results, stdout(), row.names = FALSE)