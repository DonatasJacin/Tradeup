import requests
import pandas as pd

url = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
r = requests.get(url)

print("Status code:", r.status_code)

r.raise_for_status()  # Raises exception if not 200

data = r.json()
print(f"Loaded {len(data)} skin entries.")

# Filter out covert and contraband
filtered = []
for item in data:
    rarity = item.get("rarity", {}).get("name")
    if item.get("name")[0] == "★":
        continue
    if rarity not in ("Contraband", "Extraordinary"):
        filtered.append({
            "name": item.get("name"),
            "weapon": item["weapon"]["name"],
            "collection": item["collections"][0]["name"] if item.get("collections") else None,
            "rarity": rarity,
            "float_min": item.get("min_float"),
            "float_max": item.get("max_float"),
            "tradeup_to": {
                "Industrial Grade": "Mil-Spec",
                "Mil-Spec": "Restricted",
                "Restricted": "Classified",
                "Classified": "Covert"
            }.get(rarity)
        })

print("Total skins:", len(data))
print("Filtered skins (non-Knife/Glove):", len(filtered))

df = pd.DataFrame(filtered)

# Save to disk
df.to_json("cs2_skins_metadata_full.json", orient="records", indent=2)
