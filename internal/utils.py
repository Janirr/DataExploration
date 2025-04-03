"""
An internal module containing various utilities like constant lists or data loading functions.
"""
import os
import fastf1
import pandas as pd

def load_csv_data(directory: str) -> dict[pd.DataFrame]:
    """
    Load all F1-related .csv files from a given path.
    """
    sessions = {}
    for filename in os.listdir(directory):
        if filename.lower().startswith("formula"):
            with open(f"{directory}/{filename}", encoding='utf-8') as f:
                key = filename.split("_")[-1][:-4]
                if not isinstance(sessions.get(key), pd.DataFrame):
                    sessions[key] = pd.DataFrame()
                sessions[key] = pd.concat([sessions[key], pd.read_csv(f)], axis=0)
    return sessions

years = [2019, 2020, 2021, 2022, 2023, 2024]
races = ['FP1', 'FP2', 'FP3', 'Qualifying', 'Race']
def load_fastf1_data() -> dict:
    """
    Load data of all F1 rounds since 2019, basing on the FastF1 module.
    """
    session_list = []
    for year in years:
        break_flag = 0
        for i in range(1, 100):
            for race in races:
                try:
                    session_list.append(fastf1.get_session(year, i, race))
                except ValueError:
                    # print(f"{year} had {i} rounds.")
                    break_flag = 1
                    break
            if break_flag == 1:
                break
    return session_list