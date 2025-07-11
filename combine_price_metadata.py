import pandas as pd
import json

# Load the price dataset from Skinport
price_df = pd.read_csv("skinport_cache.csv")

# Load the metadata JSON
with open("cs2_skins_metadata_full.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Convert metadata JSON to DataFrame
meta_df = pd.DataFrame(metadata)

# Rename 'name' in metadata to match 'base_name' in skinport dataset
meta_df = meta_df.rename(columns={"name": "base_name"})

# Merge the two datasets on base_name
merged_df = price_df.merge(meta_df, on="base_name", how="inner")

# Identify and log unmatched base_names
unmatched_df = price_df[~price_df["base_name"].isin(meta_df["base_name"])]

print(f"⚠️ {len(unmatched_df)} unmatched skins. Writing to 'unmatched_skins.csv'")
unmatched_df.to_csv("unmatched_skins.csv", index=False)

# Save the merged dataset
merged_df.to_csv("merged_skin_data.csv", index=False)
print("✅ Combined dataset saved as 'merged_skin_data.csv'")
