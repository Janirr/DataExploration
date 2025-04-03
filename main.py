import fastf1
import pandas as pd
import internal.utils as utils

# Load .csv data
DATA_PREFIX = "data-f1"
csv_sessions = utils.load_csv_data(DATA_PREFIX)
print(csv_sessions['drivers'].describe())

# Load fastf1 data
# fastf1_session_list = utils.load_fastf1_data()
# session = fastf1_session_list[-1]
# session.load()
# print(session.laps['LapTime'].describe())
