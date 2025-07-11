import pandas as pd
import itertools
import logging
import os

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Float midpoint definitions
WEAR_MIDPOINTS = {
    "Factory New": 0.035,
    "Minimal Wear": 0.11,
    "Field-Tested": 0.265,
    "Well-Worn": 0.415,
    "Battle-Scarred": 0.725
}

rarity_order = ['Consumer', 'Industrial', 'Mil-Spec', 'Restricted', 'Classified', 'Covert']

base_df = pd.read_csv("merged_skin_data.csv")

def get_outputs_for_skin(input_collection, rarity):
    try:
        next_rarity = rarity_order[rarity_order.index(rarity) + 1]
    except IndexError:
        return []

    outputs = base_df[
        (base_df['collection'] == input_collection) &
        (base_df['rarity'] == next_rarity)
    ]

    # Deduplicate by base_name
    outputs_unique = outputs.drop_duplicates(subset="base_name")

    return outputs_unique.to_dict('records')


# Wear brackets used in CS2
wear_brackets = [
    ("Factory New", 0.00, 0.07),
    ("Minimal Wear", 0.07, 0.15),
    ("Field-Tested", 0.15, 0.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.45, 1.00)
]

def get_wear_name(output_float):
    for wear, low, high in wear_brackets:
        if low <= output_float <= high:
            return wear
    return None  # Should never happen unless float is out of [0, 1]


def get_matching_wear(skin_rows, avg_float):
    for _, row in skin_rows.iterrows():
        if row['float_min'] <= avg_float <= row['float_max']:
            return row
    return None  # If not found

from collections import Counter

def simulate_tradeup(input_skins):
    avg_float = sum(skin[3] for skin in input_skins) / 10
    bag = []

    for skin in input_skins:
        _, collection, rarity, _, _ = skin
        outputs = get_outputs_for_skin(collection, rarity)
        for output_skin in outputs:
            bag.append(output_skin['base_name'])

    output_counts = Counter(bag)
    total_marbles = len(bag)

    expected_value = 0
    breakdown_lines = []

    for base_name, count in output_counts.items():
        prob = count / total_marbles
        matching_rows = base_df[base_df['base_name'] == base_name]
        if matching_rows.empty:
            continue

        float_min = matching_rows.iloc[0]['float_min']
        float_max = matching_rows.iloc[0]['float_max']
        output_float = (float_max - float_min) * avg_float + float_min
        wear_name = get_wear_name(output_float)

        final_row = matching_rows[matching_rows['wear'] == wear_name]
        if final_row.empty:
            continue

        market_name = final_row.iloc[0]['market_hash_name']
        price = final_row.iloc[0]['min_price']
        if pd.isna(price):
            continue

        expected_value += prob * price
        breakdown_lines.append(
            f"{market_name} @ {output_float:.4f} ({prob:.2%}) → £{price:.2f}"
        )

    total_input_cost = sum(skin[4] for skin in input_skins)
    roi = expected_value / total_input_cost if total_input_cost > 0 else 0
    output_breakdown = "; ".join(breakdown_lines)
    return expected_value, total_input_cost, roi, output_breakdown



input_skins = [
    ["AK-47 | Searing Rage", "The Fever Collection", "Classified", 0.25, 3.03],
    ["AK-47 | Searing Rage", "The Fever Collection", "Classified", 0.25, 3.03],
    ["AK-47 | Case Hardened", "The Arms Deal Collection", "Classified", 0.20, 169.14],
    ["AK-47 | Case Hardened", "The Arms Deal Collection", "Classified", 0.20, 169.14],
    ["AK-47 | Case Hardened", "The Arms Deal Collection", "Classified", 0.20, 169.14],
    ["M4A4 | Hellish", "The Train 2025 Collection", "Classified", 0.3, 22],
    ["M4A4 | Hellish", "The Train 2025 Collection", "Classified", 0.3, 22],
    ["M4A4 | Hellish", "The Train 2025 Collection", "Classified", 0.3, 22],
    ["M4A4 | Hellish", "The Train 2025 Collection", "Classified", 0.3, 22],
    ["M4A4 | Hellish", "The Train 2025 Collection", "Classified", 0.3, 22]
]

exp_value, cost, roi, breakdown = simulate_tradeup(input_skins) 


output_csv = "profitable_tradeups.csv"
if not os.path.exists(output_csv):
    pd.DataFrame(columns=["ROI", "Expected Value", "Cost", "Input Skins", "Output Breakdown"]).to_csv(output_csv, index=False)

rarities_to_test = ["Classified", "Restricted", "Mil-Spec"]

for rarity in rarities_to_test:
    collections = base_df[base_df["rarity"] == rarity]["collection"].unique()
    
    for collection in collections:
        skins = base_df[(base_df["rarity"] == rarity) & (base_df["collection"] == collection)]
        skins = skins.sort_values(by="min_price")
        
        for _, skin_row in skins.iterrows():
            skin_name = skin_row["market_hash_name"]
            base_name = skin_row["base_name"]
            price = skin_row["min_price"]
            float_min = skin_row["float_min"]
            float_max = skin_row["float_max"]

            for condition, mid_float in WEAR_MIDPOINTS.items():
                # Only look for skins in this specific wear bracket
                matching_variant = base_df[
                    (base_df["base_name"] == skin_row["base_name"]) &
                    (base_df["wear"] == condition)
                ]

                if matching_variant.empty:
                    continue

                row = matching_variant.iloc[0]
                if not (row["float_min"] <= mid_float <= row["float_max"]):
                    continue

                market_name = row["market_hash_name"]
                variant_price = row["min_price"]

                input_skins = [[market_name, collection, rarity, mid_float, variant_price]] * 10

                exp_value, cost, roi, breakdown = simulate_tradeup(input_skins)

                if roi >= 0.9:
                    row = {
                        "ROI": f"{roi:.2%}",
                        "Expected Value": f"£{exp_value:.2f}",
                        "Cost": f"£{cost:.2f}",
                        "Input Skins": str(input_skins),
                        "Output Breakdown": breakdown
                    }
                    print(row)
                    pd.DataFrame([row]).to_csv(output_csv, mode="a", header=False, index=False)

# Final sort of profitable_tradeups.csv by ROI descending
df = pd.read_csv(output_csv)

# Clean just the ROI column
df["ROI_clean"] = df["ROI"].str.replace("%", "", regex=False).astype(float)

# Sort and drop helper column
df = df.sort_values(by="ROI_clean", ascending=False).drop(columns=["ROI_clean"])

# Save sorted results
df.to_csv(output_csv, index=False)

