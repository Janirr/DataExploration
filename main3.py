from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from scipy.stats import spearmanr
import internal.utils as utils
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

# Wczytaj dane
omni_df = pd.read_csv("omni_results_data.csv")
speed_df = pd.read_csv("omni_speed_data.csv")
weather_df = pd.read_csv("omni_weather_summary.csv")
corners_df = pd.read_csv("corner_type_summary.csv")

# Merge all
avg_speed_gap_per_race = speed_df.groupby(['Year', 'GrandPrix'])['AvgSpeedGap'].mean().reset_index()

print(speed_df.columns.tolist())
speed_df = speed_df.rename(columns={"Driver": "Abbreviation"})
final_df = omni_df.merge(
    speed_df[["Year", "GrandPrix", "Abbreviation", "AvgSpeedGap"]],
    on=["Year", "GrandPrix", "Abbreviation"],
    how="left"
).merge(
    weather_df[["Year", "GrandPrix", "Avg Air Temp (°C)", "Avg Track Temp (°C)", "Avg Wind Speed (m/s)", "Rainfall Fraction"]],
    on=["Year", "GrandPrix"],
    how="left"
).merge(
    corners_df[["Year", "GrandPrix", "NumFastCorners", "NumMediumCorners", "NumSlowCorners"]],
    on=["Year", "GrandPrix"],
    how="left"
)

# Uporządkuj dane
final_df = final_df.dropna(subset=['ClassifiedPosition'])  # Remove DNFs

# Zamień pozycje klasyfikacji na liczbowe
final_df["ClassifiedPosition"] = pd.to_numeric(final_df["ClassifiedPosition"], errors="coerce")
final_df = final_df.dropna(subset=["ClassifiedPosition"])

# Zakoduj kierowców (opcjonalnie)
print("Kolumny w omni_df:", omni_df.columns.tolist())
driver_encoder = LabelEncoder()
final_df["DriverEncoded"] = driver_encoder.fit_transform(final_df["Abbreviation"])

# Przygotuj dane treningowe
features = [
    'AvgSpeedGap',
    'Avg Air Temp (°C)', 'Avg Track Temp (°C)', 'Avg Wind Speed (m/s)', 'Rainfall Fraction',
    'NumFastCorners', 'NumMediumCorners', 'NumSlowCorners'
]

year_to_test = 2019  # Zmień na odpowiedni dostępny rok
gp_name = 'Australian Grand Prix'

train_df = final_df[(final_df['GrandPrix'] != gp_name) | (final_df['Year'] != year_to_test)]
test_df = final_df[(final_df['GrandPrix'] == gp_name) & (final_df['Year'] == year_to_test)]

X_train = train_df[features]
y_train = train_df['ClassifiedPosition']
X_test = test_df[features]

# Trenuj model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Przewidź klasyfikację
test_df['PredictedPosition'] = model.predict(X_test)

# Ranking: im niższy wynik, tym wyższa pozycja
test_df = test_df.sort_values(by='PredictedPosition').reset_index(drop=True)
test_df['PredictedRank'] = test_df.index + 1

# Oblicz korelację Spearmana
spearman_corr, _ = spearmanr(test_df['ClassifiedPosition'], test_df['PredictedRank'])

print(f"Spearman correlation: {spearman_corr:.3f}")
print(test_df[['Abbreviation', 'ClassifiedPosition', 'PredictedRank']])

print("=========== Speed Data ===========")
print(final_df.head(40))
