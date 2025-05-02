import internal.utils as utils
import pandas as pd
import numpy as np

# Load fastf1 data
fastf1_sessions = utils.load_fastf1_data()
session = fastf1_sessions['Race'][0] #2nd race from 2022-2025
print("\n\n", session, "\n\n")
session.load(weather=True, laps=True, telemetry=True)

# Laps - Top speed
"""
Time (pandas.Timedelta): Session time at which the lap was set (i.e. finished)
LapTime (pandas.Timedelta): Lap time of the last finished lap (the lap in this row)
Driver (str): Driver number
NumberOfLaps (int): Number of laps driven by this driver including the lap in this row
NumberOfPitStops (int): Number of pit stops of this driver
PitInTime (pandas.Timedelta): Session time at which the driver entered the pits. Consequently, if this value is not NaT the lap in this row is an inlap.
PitOutTime (pandas.Timedelta): Session time at which the driver exited the pits. Consequently, if this value is not NaT, the lap in this row is an outlap.
Sector1/2/3Time (pandas.Timedelta): Sector times (one column for each sector time)
Sector1/2/3SessionTime (pandas.Timedelta): Session time at which the corresponding sector time was set (one column for each sector’s session time)
SpeedI1/I2/FL/ST: Speed trap speeds; FL is speed at the finish line; I1 and I2 are speed traps in sector 1 and 2 respectively; ST maybe a speed trap on the longest straight (?)
"""
laps = session.laps
laps = laps.reset_index(drop=True)


laps_clean = laps[['Time', 'Driver', 'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']].dropna()
# Calculate average speed trap for each driver
average_speed = laps_clean.groupby('Driver').mean().reset_index()
average_speed['AverageSpeed'] = average_speed[['SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']].mean(axis=1)
# Sort by AverageSpeed in descending order
average_speed_sorted = average_speed.sort_values(by='AverageSpeed', ascending=False).reset_index(drop=True)
print("\nAverage Speed Trap for each driver (sorted):\n", average_speed_sorted)

# Weather
"""
#Time (datetime.timedelta): session timestamp (time only)
# AirTemp (float): Air temperature [°C]
# Humidity (float): Relative humidity [%]
# Pressure (float): Air pressure [mbar]
# Rainfall (bool): Shows if there is rainfall
# TrackTemp (float): Track temperature [°C]
# WindDirection (int): Wind direction [°] (0°-359°)
# WindSpeed (float): Wind speed [m/s]
"""
weather_data = session.weather_data
weather_data = weather_data.reset_index(drop=True)
# Drop any rows with NaN in relevant columns to avoid skewing averages
weather_data_clean = weather_data[['AirTemp', 'TrackTemp', 'Rainfall', 'WindSpeed']].dropna()

# Compute averages
average_air_temp = weather_data_clean['AirTemp'].mean()
average_track_temp = weather_data_clean['TrackTemp'].mean()
average_wind_speed_temp = weather_data_clean['WindSpeed'].mean()

# For rainfall, you can compute:
# - Fraction of time it rained (boolean True treated as 1, False as 0)
# - Or count of rainy intervals
rainfall_fraction = weather_data_clean['Rainfall'].mean()  # Between 0 and 1
rainfall_count = weather_data_clean['Rainfall'].sum()      # Total number of rainy intervals

print(f"Average Wind Speed: {average_wind_speed_temp:.2f} m/s")
print(f"Average Air Temperature: {average_air_temp:.2f} °C")
print(f"Average Track Temperature: {average_track_temp:.2f} °C")
print(f"Rainfall occurred in {rainfall_fraction*100:.1f}% of intervals ({int(rainfall_count)} times)")

# Results
"""
DriverNumber | str | The number associated with this driver in this session (usually the drivers permanent number)
BroadcastName | str | First letter of the drivers first name plus the drivers full last name in all capital letters.
FullName | str | The drivers full name (e.g. “Pierre Gasly”)
Abbreviation | str | The drivers three letter abbreviation (e.g. “GAS”)
DriverId | str | driverId that is used by the Ergast API
TeamName | str | The team name (short version without title sponsors)
TeamColor | str | The color commonly associated with this team (hex value)
TeamId | str | constructorId that is used by the Ergast API
FirstName | str | The drivers first name
LastName | str | The drivers last name
HeadshotUrl | str | The URL to the drivers headshot
CountryCode | str | The drivers country code (e.g. “FRA”)
Position | float | The drivers finishing position
ClassifiedPosition | str | The official classification result for each driver. This is either an integer value if the driver is officially classified or one of “R” (retired), “D” (disqualified), “E” (excluded), “W” (withdrawn), “F” (failed to qualify) or “N” (not classified).
GridPosition | float | The drivers starting position
Q1 | pd.Timedelta | The drivers best Q1 time 
Q2 | pd.Timedelta | The drivers best Q2 time 
Q3 | pd.Timedelta | The drivers best Q3 time 
Time | pd.Timedelta | The drivers total race time
Status | str | A status message to indicate if and how the driver finished the race or to indicate the cause of a DNF. Possible values include but are not limited to Finished, + 1 Lap, Crash, Gearbox
Points | float | The number of points received by each driver for their finishing result.
"""
results = session.results[['Abbreviation','TeamName', 'ClassifiedPosition', 'GridPosition', 'Time', 'Status', 'Points']]

# Skopiuj dane wyników
df = results.copy()

# Upewnij się, że Time jest typu timedelta
df['Time'] = pd.to_timedelta(df['Time'], errors='coerce')

# Lider
leader_row = df[df['ClassifiedPosition'] == '1'].iloc[0]
leader_time = leader_row['Time']

# Liczba okrążeń lidera
laps_completed = session.laps[session.laps['Driver'] == leader_row['Abbreviation']].shape[0]

# Średni czas okrążenia lidera
avg_lap_time = leader_time / laps_completed
avg_lap_time_ms = avg_lap_time.total_seconds() * 1000

# Funkcja normalizacji czasu
def normalize_time(row):
    status = str(row['Status'])
    pos = str(row['ClassifiedPosition'])
    grid = str(row['GridPosition']) 
    
    # Lider -> 0
    if pos == '1':
        return 0.0

    # Ukończony wyścig — Time to strata do lidera
    if status == 'Finished' and pd.notnull(row['Time']):
        return row['Time'].total_seconds() * 1000
    
    # Zdublowani kierowcy
    elif '+1 Lap' in status or '+2 Laps' in status or '+3 Laps' in status:
        try:
            laps_behind = int(status.split()[0][1])
            return laps_behind * avg_lap_time_ms + int(pos) * 5000
        except:
            return np.nan
    
    # Inne przypadki (DNF)
    else:
        return avg_lap_time_ms * float(grid) / 5

# Zastosuj normalizację
df['GapToLeaderMs'] = df.apply(normalize_time, axis=1)

# Posortuj po pozycji końcowej
df = df.sort_values(by='GapToLeaderMs')

# Wyświetl końcowy wynik
print(df[['Abbreviation','TeamName', 'ClassifiedPosition', 'GridPosition', 'Status', 'Points', 'GapToLeaderMs']])