
import pandas as pd

# Load the CSV file into a DataFrame
omni_weather_df = pd.read_csv("omni_weather_data.csv")


# Group by Year and Grand Prix, then compute the required averages
weather_summary_df = (
    omni_weather_df
    .groupby(['Year', 'GrandPrix'])
    .agg({
        'AirTemp': 'mean',
        'TrackTemp': 'mean',
        'WindSpeed': 'mean',
        'Rainfall': ['mean', 'sum']  # mean = fraction, sum = count of True
    })
)

# Flatten the MultiIndex columns
weather_summary_df.columns = [
    'Avg Air Temp (°C)',
    'Avg Track Temp (°C)',
    'Avg Wind Speed (m/s)',
    'Rainfall Fraction',
    'Rainfall Count'
]

# Reset index to get Year and GrandPrix as columns
weather_summary_df = weather_summary_df.reset_index()

# View the result
print(weather_summary_df)

weather_summary_df.to_csv("omni_weather_summary.csv", index=False)