import fastf1
import pandas as pd
import internal.utils as utils

# Load .csv data
DATA_PREFIX = "data-f1"
csv_sessions = utils.load_csv_data(DATA_PREFIX)
drivers = csv_sessions['drivers']
verstappen = drivers.loc[drivers['Abbreviation'] == 'VER']

print(verstappen)

# Load fastf1 data
fastf1_sessions = utils.load_fastf1_data()
session = fastf1_sessions['Race'][2]
print("\n\n", session, "\n\n")
session.load()
print(session.get_driver('HAM'))
