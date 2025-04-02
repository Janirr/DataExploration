import os
import fastf1
import pandas as pd

years = [2019, 2020, 2021, 2022, 2023, 2024]
races = ['FP1', 'FP2', 'FP3', 'Qualifying', 'Race']
DATA_PREFIX = "data-f1"

# Load .csv data
csv_session_list = []
for filename in os.listdir(DATA_PREFIX):
    if filename.lower().startswith("formula"):
        with open(f"{DATA_PREFIX}/{filename}", encoding='utf-8') as f:
            csv_session_list.append(pd.read_csv(f))
for element in csv_session_list:
    print(element)
# Load fastf1 data
fastf1_session_list = []
for year in years:
    break_flag = 0
    for i in range(1, 100):
        for race in races:
            try:
                fastf1_session_list.append(fastf1.get_session(year, i, race))
            except ValueError:
                print(f"{year} had {i} rounds.")
                break_flag = 1
                break
        if break_flag == 1:
            break

session = fastf1_session_list[-1]
session.load()
print(session.laps['LapTime'].describe())
