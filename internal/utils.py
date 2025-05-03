"""
An internal module containing various utilities like constants or data loading functions.
"""
import os
import fastf1
import pandas as pd
import numpy as np

# Set pandas display options to show all columns and rows
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)  # Show all rows (be cautious with large datasets)
pd.set_option('display.width', None)  # Adjust to the screen width


def load_csv_data(directory: str) -> dict[pd.DataFrame]:
    """
    Load all F1-related .csv files from a given path.
    """
    sessions = {}
    for filename in os.listdir(directory):
        if filename.lower().startswith("formula"):
            with open(f"{directory}/{filename}", encoding='utf-8') as f:
                flavor_data = filename.split("_")
                key = flavor_data[-1][:-4]
                if not isinstance(sessions.get(key), pd.DataFrame):
                    sessions[key] = pd.DataFrame()
                this_years_dataframe = pd.read_csv(f)
                this_years_dataframe['Year'] = flavor_data[-2].removesuffix('season')
                sessions[key] = pd.concat([sessions[key], this_years_dataframe], axis=0)
    return sessions

# via official documentation:
# session name abbreviation: 'FP1', 'FP2', 'FP3', 'Q', 'S', 'SS', 'SQ', 'R'
# full session name: 'Practice 1', 'Practice 2', 'Practice 3', 'Sprint', 'Sprint Shootout', 'Sprint Qualifying', 'Qualifying', 'Race'; provided names will be normalized, so that the name is case-insensitive
# number of the session: 1, 2, 3, 4, 5
typesOfSessions = ['FP1', 'FP2', 'FP3', 'Qualifying', 'Race']
years = [2019, 2020, 2021, 2022, 2023, 2024]
def load_fastf1_data() -> dict:
    """
    Load data of all F1 rounds since 2019, basing on the FastF1 module.
    """
    sessions = {x: [] for x in typesOfSessions}
    for year in years:
        break_flag = 0
        for i in range(1, 26):
            for sessionType in typesOfSessions:
                try:
                    session = fastf1.get_session(year, i, sessionType)
                    sessions[sessionType].append(session)
                except ValueError:
                    break_flag = 1
                    break
            if break_flag == 1:
                break
    return sessions

# Time normalization function
def normalize_time(row, avg_lap_time_ms: float) -> float:
    status = str(row['Status'])
    pos = str(row['ClassifiedPosition'])
    grid = str(row['GridPosition']) 
    
    # Leader -> 0
    if pos == '1':
        return 0.0

    # Finished race — Time to gap to leader
    if status == 'Finished' and pd.notnull(row['Time']):
        return row['Time'].total_seconds() * 1000
    
    # Lapped drivers
    elif '+1 Lap' in status or '+2 Laps' in status or '+3 Laps' in status:
        try:
            laps_behind = int(status.split()[0][1])
            return laps_behind * avg_lap_time_ms + int(pos) * 5000
        except:
            return np.nan
    
    # Other cases (DNF)
    else:
        return avg_lap_time_ms * float(grid) / 5

if __name__ == "__main__":
    print("This module (internal/utils.py) is not meant to be used on its own.")