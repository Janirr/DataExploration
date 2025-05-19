import pandas as pd

# Load the CSV files
drivers = pd.read_csv("data-f1/kaggle/drivers.csv")
qualifying = pd.read_csv("data-f1/kaggle/qualifying.csv")
races = pd.read_csv("data-f1/kaggle/races.csv")

# Merge qualifying with drivers on driverId
qual_with_drivers = pd.merge(qualifying, drivers, on="driverId", how="left")

# Merge the result with races on raceId
merged_df = pd.merge(qual_with_drivers, races, on="raceId", how="left")

# Select and rename relevant columns
result = merged_df[[
    "code", "name", "year", "q1", "q2", "q3"
]].rename(columns={
    "code": "Driver code",
    "name": "Race name",
    "year": "Race year",
    "q1": "Q1",
    "q2": "Q2",
    "q3": "Q3"
})

result["Race year"] = result["Race year"].astype(int)
result.to_csv("qualifying_results_cleaned.csv", index=False)
# Display the resulting DataFrame
print(result)
