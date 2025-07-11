import requests

API_KEY = "your_api_key_here"
HEADERS = {
    "Authorization": API_KEY,
    "User-Agent": "Mozilla/5.0"
}

url = "https://csfloat.com/api/v1/listings?market_hash_name=AK-47%20%7C%20Slate%20(Field-Tested)&page=0&limit=50&type=buy_now&sort_by=lowest_price"

r = requests.get(url, headers=HEADERS)
print("Status:", r.status_code)
print("Text:", r.text[:500])  # Print sample response or error
