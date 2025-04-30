import requests
import time
import random
import pandas as pd
from datetime import datetime, timedelta

# Define the wait time between each request in seconds
WAIT_TIME = 2  # Change this value as needed

# Define the number of cities to test (set to None to test all)
NUM_CITIES_TO_TEST = 5  # Change this value as needed, or set to None to test all

# Load cities from CSV
df_cities = pd.read_csv("CitiesToScrape.csv")

# If NUM_CITIES_TO_TEST is set, take a subset of the DataFrame
if NUM_CITIES_TO_TEST is not None:
    df_cities = df_cities.head(NUM_CITIES_TO_TEST)

# Generate Penske-style window_name
def generate_window_name():
    base = ''
    conversion_factor = int(time.time() * 1000)
    for _ in range(4):
        base += format(random.randint(0, conversion_factor), 'x')
    return 'RENTALWIN' + base

# Final normalized truck names mapping
truck_name_mapping = {
    "Electric High Roof Cargo Van": "High Roof Cargo Van",
    "High Roof Cargo Van": "High Roof Cargo Van",
    "Cargo Van": "High Roof Cargo Van",
    "Panel Van": "High Roof Cargo Van",
    "12 Foot Truck": "12 Foot Truck",
    "16 Foot Truck": "16 Foot Truck",
    "16 Foot Cube Van": "16 Foot Truck",
    "26 Foot Truck": "26 Foot Truck",
}

# Initialize output
all_rows = []

# Define lead times
lead_times = [1, 7, 14]

for index, row in df_cities.iterrows():
    CITY_NAME = row["city"]
    STATE_NAME = row["state"]
    COUNTRY_NAME = row["country"]
    lat = row["lat"]
    lon = row["lon"]

    for lead_time in lead_times:
        pickup_date = (datetime.now() + timedelta(days=lead_time)).strftime('%Y-%m-%d')
        dropoff_date = (datetime.now() + timedelta(days=lead_time + 1)).strftime('%Y-%m-%d')

        # === Session setup
        WINDOW_NAME = generate_window_name()
        CLIENT_ID = "bbc9ee1c9e934dfa507a8f8e750ef66f"
        session = requests.Session()
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.pensketruckrental.com",
            "referer": "https://www.pensketruckrental.com/",
            "x-ibm-client-id": CLIENT_ID,
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        # 1. RULE DATA
        rule_data_url = f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/rule-data?cache={int(time.time() * 1000)}&window_name={WINDOW_NAME}"
        session.post(rule_data_url, headers=headers, json={
            "screenWidth": 1806,
            "screenHeight": 1271,
            "country": COUNTRY_NAME,
        })

        # 2. CUSTOMER PROFILE
        customer_profile_url = f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/features/customer-profile-activation-switch?cache={int(time.time() * 1000)}&window_name={WINDOW_NAME}"
        session.get(customer_profile_url, headers=headers)

        # 3. LOCATION DURATION
        location_duration_url = f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/location-duration?cache={int(time.time() * 1000)}&window_name={WINDOW_NAME}"
        session.post(location_duration_url, headers=headers, json={
            "country": COUNTRY_NAME.lower(),
            "dropoffLocationSearch": {"address": ""},
            "pickupLocationSearch": {
                "latitude": lat,
                "longitude": lon,
                "address": f"{CITY_NAME}, {STATE_NAME}, {COUNTRY_NAME}",
                "city": CITY_NAME,
                "state": STATE_NAME,
                "zip": None
            },
            "rentalType": "local",
            "screenHeight": 1271,
            "screenWidth": 1806
        })

        # 4. NEW QUOTE
        new_quote_url = f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/new-quote?cache={int(time.time() * 1000)}&window_name={WINDOW_NAME}"
        session.post(new_quote_url, headers=headers, json={
            "pickupDate": pickup_date,
            "dropOffDate": dropoff_date
        })

        # 5. QUOTE SUMMARY
        quote_summary_url = f"https://api.pensketruckrental.com/b2b/consumererental/api/v2/quote/summary?cache={int(time.time() * 1000)}&window_name={WINDOW_NAME}"
        response = session.get(quote_summary_url, headers=headers)
        data = response.json()

        # === Format into single row
        row = {}
        for truck in data.get("data", {}).get("trucks", []):
            raw_name = truck.get("truckName") or truck.get("details", {}).get("description")
            normalized_name = truck_name_mapping.get(raw_name)
            if not normalized_name:
                continue
            if normalized_name == "18 Foot Truck":
                continue  # Ignore 18 Foot Truck

            day_rate = truck.get("dayRate")
            mileage_rate = truck.get("mileagePrice")
            selectable = truck.get("blockingRules", {}).get("selectable", "N")

            row[f"{normalized_name} - Day Rate"] = day_rate
            row[f"{normalized_name} - Mileage Rate"] = mileage_rate
            row[f"{normalized_name} - Bookable"] = (selectable == "Y")

        row["City"] = CITY_NAME
        row["State"] = STATE_NAME
        row["Lead Time"] = lead_time
        row["Pickup Date"] = pickup_date
        all_rows.append(row)

        # Wait for the specified time before the next request
        time.sleep(WAIT_TIME)

# === Final DataFrame
df = pd.DataFrame(all_rows)
df.set_index(["City", "State"], inplace=True)
pd.set_option("display.max_columns", None)

display(df)

# Save the CSV file to the new folder with the current date in the file name
current_date = datetime.now().strftime('%Y-%m-%d')
file_name = f"penske_rates_{current_date}.csv"
df.to_csv(f"{file_name}")
