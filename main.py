import internal.utils as utils
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

# Load fastf1 data
fastf1_sessions = utils.load_fastf1_data()
# session = fastf1_sessions['Race'][0] #2nd race from 2022-2025
omni_weather_df, omni_results_df, omni_speed_df, omni_corners_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

for session in fastf1_sessions['Race'][:10]:
    # Session name format is as follows:
    # [YEAR] Season Round [ROUND NO]: [GRAND PRIX NAME] - [information regarding whether the session is a practice session, qualifying race or the main race itself]

    # Extract the year of the race from session name
    year = int(str(session)[:5])
    # Extract the grand prix name from the session name
    grand_prix = str(session).split(':')[1].split('-')[0].strip()

    session.load(weather=True, laps=True, telemetry=True)


    # print("=========== Session ===========")
    # print(session, "\n")

    # Weather
    """
    # Time (datetime.timedelta): session timestamp (time only)
    # AirTemp (float): Air temperature [°C]
    # Humidity (float): Relative humidity [%]
    # Pressure (float): Air pressure [mbar]
    # Rainfall (bool): Shows if there is rainfall
    # TrackTemp (float): Track temperature [°C]
    # WindDirection (int): Wind direction [°] (0°-359°)
    # WindSpeed (float): Wind speed [m/s]
    """
    try:
        weather_data = session.weather_data
        weather_data = weather_data.reset_index(drop=True)
        # Drop any rows with NaN in relevant columns to avoid skewing averages
        weather_df = weather_data[['AirTemp', 'TrackTemp', 'Rainfall', 'WindSpeed']].dropna()
        weather_df['Year'], weather_df['GrandPrix'] = year, grand_prix
        # Append to the general weather dataframe
        omni_weather_df = pd.concat([omni_weather_df, weather_df])
    except:
        pass


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
    try:
        laps = session.laps
        laps = laps.reset_index(drop=True)


        laps_clean = laps[['Time', 'Driver', 'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']].dropna()
        # Calculate average speed trap for each driver
        average_speed = laps_clean.groupby('Driver').mean().reset_index()
        average_speed['AverageSpeed'] = average_speed[['SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']].mean(axis=1)
        # Sort by AverageSpeed in descending order
        speed_df = average_speed.sort_values(by='AverageSpeed', ascending=False).reset_index(drop=True)
        # print("=========== Top speeds ===========")
        # print("Average Speed Trap for each driver (sorted):\n", speed_df,"\n")
        speed_df['AvgSpeedGap'] = speed_df['AverageSpeed'][0] - speed_df['AverageSpeed']

        # Append to the general speed dataframe
        speed_df['Year'], speed_df['GrandPrix'] = year, grand_prix
        omni_speed_df = pd.concat([omni_speed_df, speed_df])
    except:
        pass

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
    try:
        results = session.results[['DriverNumber', 'Abbreviation','TeamName', 'ClassifiedPosition', 'GridPosition', 'Time', 'Status', 'Points']]

        # Copy the results data
        results_df = results.copy()

        # Ensure that Time is timedelta type
        results_df['Time'] = pd.to_timedelta(results_df['Time'], errors='coerce')

        # Leader
        leader_filter = results_df[results_df['ClassifiedPosition'] == '1']
        if not leader_filter.empty:
            leader_row = leader_filter.iloc[0]
            leader_time = leader_row['Time']
            laps_completed = session.laps[session.laps['Driver'] == leader_row['Abbreviation']].shape[0]
            avg_lap_time = leader_time / laps_completed
            avg_lap_time_ms = avg_lap_time.total_seconds() * 1000
            results_df['GapToLeaderMs'] = results_df.apply(lambda row: utils.normalize_time(row, avg_lap_time_ms), axis=1)
        else:
            print(f"No leader found for session {year} {grand_prix}. Skipping GapToLeader calculation.")
            results_df['GapToLeaderMs'] = np.nan

        # Sort by final position
        # results_df = results_df.sort_values(by='GapToLeaderMs')

        # Display final results
        # print("=========== Results ===========")
        # print(results_df[['Abbreviation','TeamName', 'ClassifiedPosition', 'GridPosition', 'Status', 'Points', 'GapToLeaderMs']],"\n")
        
        # Append to the general results dataframe
        results_df['Year'], results_df['GrandPrix'] = year, grand_prix
        omni_results_df = pd.concat([omni_results_df, results_df])
    except:
        pass

    try:
        # Circuit Info - number of corners, length, etc.
        circuit_info = session.get_circuit_info()

        # Access the 'corners' DataFrame from the CircuitInfo object
        corners_df = circuit_info.corners

        # Append to the general corner dataframe
        corners_df['Year'], corners_df['GrandPrix'] = year, grand_prix
        omni_corners_df = pd.concat([omni_corners_df, corners_df])

        # Extract only the 'Angle' and 'Distance' columns
        circuit_info_filtered = corners_df[['Angle', 'Distance']]
    except:
        pass

    # Print the filtered information
    # print("=========== Track data (corners) ===========")
    # print(circuit_info_filtered)
    # print(f"Number of corners: {circuit_info_filtered.shape[0]}")

    # TODO: Combine all data frames and repeat it for all sessions
    # GAUSS: I'm not sure what was meant by "combining all data frames",
    #        but I have created a loop which handles extracting data from
    #        all available sessions.

# Compute global weather averages
average_air_temp = omni_weather_df['AirTemp'].mean()
average_track_temp = omni_weather_df['TrackTemp'].mean()
average_wind_speed_temp = omni_weather_df['WindSpeed'].mean()

# For rainfall, you can compute:
# - Fraction of time it rained (boolean True treated as 1, False as 0)
# - Or count of rainy intervals
rainfall_fraction = omni_weather_df['Rainfall'].mean()  # Between 0 and 1
rainfall_count = omni_weather_df['Rainfall'].sum()      # Total number of rainy intervals

# Ensure that Angle is numeric
omni_corners_df['Angle'] = pd.to_numeric(omni_corners_df['Angle'], errors='coerce')

# Categorize each corner by speed based on the angle
def categorize_corner(angle):
    if abs(angle) > 100:
        return 'Slow'
    elif abs(angle) > 50:
        return 'Medium'
    else:
        return 'Fast'

omni_corners_df['CornerType'] = omni_corners_df['Angle'].apply(categorize_corner)

# Group by Grand Prix and Year and count each corner type
corner_summary_df = omni_corners_df.groupby(['Year', 'GrandPrix', 'CornerType']).size().unstack(fill_value=0).reset_index()

# Rename columns for clarity
corner_summary_df.columns.name = None
corner_summary_df.rename(columns={
    'Slow': 'NumSlowCorners',
    'Medium': 'NumMediumCorners',
    'Fast': 'NumFastCorners'
}, inplace=True)

# Fill missing categories with 0 if some types are absent in some circuits
for col in ['NumSlowCorners', 'NumMediumCorners', 'NumFastCorners']:
    if col not in corner_summary_df.columns:
        corner_summary_df[col] = 0

# Save to CSV
# corner_summary_df.to_csv('corner_type_summary.csv', index=False)

# Display a preview
print(corner_summary_df.head())

print("=========== Weather Data ===========")
print(f"Average Wind Speed: {average_wind_speed_temp:.2f} m/s")
print(f"Average Air Temperature: {average_air_temp:.2f} °C")
print(f"Average Track Temperature: {average_track_temp:.2f} °C")
print(f"Rainfall occurred in {rainfall_fraction*100:.1f}% of intervals ({int(rainfall_count)} times)\n")

print("HEAD=====")
omni_weather_df = pd.read_csv('omni_weather_summary.csv')
print(omni_weather_df.head())

print("=========== Speed Data ===========")
print(omni_speed_df.head())

print("=========== Results Data ===========")
print(omni_results_df.head())

print("=========== Corners Data ===========")
print(omni_corners_df.head())

omni_weather_df.to_csv("omni_weather_data.csv", index=False)
omni_results_df.to_csv("omni_results_data.csv", index=False)
omni_speed_df.to_csv("omni_speed_data.csv", index=False)
omni_corners_df.to_csv("omni_corners_data.csv", index=False)

omni_df = omni_results_df.copy()


# Append speed DF attributes
omni_df = omni_df.merge(
    omni_speed_df[["Year", "GrandPrix", "AvgSpeedGap"]],
    on=["Year", "GrandPrix"],
    how="left"
)
# Append weather DF attributes
omni_df = omni_df.merge(
    omni_weather_df[["Year", "GrandPrix", "Avg Air Temp (°C)", "Avg Track Temp (°C)", "Avg Wind Speed (m/s)", "Rainfall Fraction", "Rainfall Count"]],
    on=["Year", "GrandPrix"],
    how="left"
)
# Append corner DF attributes
omni_df = omni_df.merge(
    corner_summary_df[["Year", "GrandPrix", "NumFastCorners", "NumMediumCorners", "NumSlowCorners"]],
    on=["Year", "GrandPrix"],
    how="left"
)

corr, p_values = spearmanr(omni_df)

# spearmanr returns a NumPy array (corr), so convert it to a DataFrame
corr_df = pd.DataFrame(corr, index=omni_df.columns, columns=omni_df.columns)

plt.figure(figsize=(8, 6))
sns.heatmap(corr_df, annot=True, cmap='Greens', center=0, square=True)
plt.title("Results DataFrame Correlation Heatmap")
plt.show()