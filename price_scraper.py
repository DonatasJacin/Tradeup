import requests
import pandas as pd
import os
import time

URL = "https://api.skinport.com/v1/items"
HEADERS = {
    "Accept-Encoding": "br",  # Required for Skinport API
    "User-Agent": "Mozilla/5.0"
}

WEAR_NAMES = [
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
    "Well-Worn",
    "Battle-Scarred"
]

CACHE_FILE = "skinport_cache.csv"

def fetch_skinport_items():
    response = requests.get(URL, headers=HEADERS, params={"app_id": 730})
    response.raise_for_status()
    return response.json()

def is_knife_or_glove(name):
    name = name.lower()
    return "knife" in name or "gloves" in name or "glove" in name or "karambit" in name or "hand wraps" in name or "bayonet" in name

def extract_skin_data(items, already_cached=set()):
    data = []

    for item in items:
        name = item.get("market_hash_name", "")
        if is_knife_or_glove(name):
            continue

        if name in already_cached:
            continue  # Skip already cached entries

        for wear in WEAR_NAMES:
            if f"({wear})" in name:
                data.append({
                    "market_hash_name": name,
                    "base_name": name.split(" (")[0],
                    "wear": wear,
                    "min_price": item.get("min_price"),
                    "suggested_price": item.get("suggested_price"),
                    "mean_price": item.get("mean_price"),
                    "quantity": item.get("quantity")
                })
                break

    return data

def load_cached_data():
    if os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE)
        print(f"🔁 Loaded {len(df)} cached rows.")
        return df
    return pd.DataFrame()

def save_to_cache(df):
    df.to_csv(CACHE_FILE, index=False)
    print(f"💾 Saved {len(df)} rows to {CACHE_FILE}")

def main():
    print("📦 Checking for cached data...")
    cached_df = load_cached_data()
    cached_names = set(cached_df["market_hash_name"]) if not cached_df.empty else set()

    print("🔄 Fetching from Skinport...")
    try:
        items = fetch_skinport_items()
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return

    new_data = extract_skin_data(items, already_cached=cached_names)
    print(f"➕ Parsed {len(new_data)} new items.")

    if new_data:
        new_df = pd.DataFrame(new_data)
        combined = pd.concat([cached_df, new_df], ignore_index=True)
        combined.sort_values(by=["base_name", "wear"], inplace=True)
        save_to_cache(combined)
    else:
        print("✅ No new data to save.")

if __name__ == "__main__":
    main()
