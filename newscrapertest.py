import requests
import time
import random
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

# === Parameters ===
WAIT_TIME_RANGE    = (1, 2)
NUM_CITIES_TO_TEST = 3
LEAD_TIMES         = [1, 7, 14]
MAX_WORKERS        = 1

# Exponential backoff
MAX_RETRIES = 5

# Throttle: minimum seconds between *all* requests
MIN_INTERVAL = 3.0
_last_request_time = 0.0

# Proxy pool: these are plain HTTP proxies.
# If any are SOCKS5, prefix them with "socks5://" instead of "http://"
PROXIES = [
    "http://15.206.25.41:1080",
    "http://47.251.122.81:8888",
    "http://47.76.144.139:4145",
    "http://47.251.87.74:10443",
    "http://36.92.193.189:80",
    "http://159.65.245.255:80",
    "http://52.194.186.70:1080",
    "http://66.201.7.151:3128",
    "http://38.54.71.67:80",
    "http://23.82.137.156:80",
    "http://50.221.74.130:80",
    "http://190.58.248.86:80",
    "http://95.216.148.196:80",
    "http://200.174.198.86:8888",
    "http://200.250.131.218:80",
    "http://87.248.129.32:80",
    "http://97.74.87.226:80",
    "http://50.231.104.58:80",
    "http://44.195.247.145:80",
    "http://15.156.24.206:3128",
    "http://13.55.210.141:3128",
    "http://14.229.229.218:8080",
    "http://3.212.148.199:3128",
    "http://107.20.192.76:3128",
    "http://54.79.171.21:3128",
    "http://54.66.27.238:3128",
    "http://15.157.30.77:3128",
    "http://35.182.47.71:3128",
    "http://3.96.92.88:3128",
    "http://15.223.105.115:3128",
    "http://3.90.100.12:80",
    "http://54.207.65.150:3128",
    "http://188.166.230.109:31028",
    "http://203.74.125.18:8888",
    "http://172.188.122.92:80",
    "http://212.33.205.55:3128",
    "http://50.217.226.47:80",
    "http://50.239.72.16:80",
    "http://54.85.222.237:3128",
    "http://50.174.7.157:80",
    "http://50.207.199.81:80",
    "http://35.154.71.72:1080",
    "http://34.143.143.61:7777",
    "http://172.167.161.8:8080",
    "http://85.105.90.104:3310",
    "http://213.230.125.2:8080",
    "http://3.108.115.48:3128",
    "http://3.97.167.115:3128",
    "http://40.76.69.94:8080",
    "http://57.128.37.47:3128",
    "http://50.223.246.237:80",
    "http://13.59.242.56:50000",
    "http://44.218.183.55:80",
    "http://50.207.199.80:80",
    "http://50.239.72.19:80",
    "http://50.175.212.74:80",
    "http://188.68.52.244:80",
    "http://185.233.118.31:8080",
    "http://13.214.14.133:8080",
    "http://35.182.168.151:3128",
    "http://52.63.129.110:3128",
    "http://52.65.193.254:3128",
    "http://3.97.176.251:3128",
    "http://3.24.125.131:3128",
    "http://13.54.47.197:80",
    "http://3.104.88.178:80",
    "http://13.55.184.26:1080",
    "http://13.237.241.71:3128",
    "http://44.219.161.194:3128",
    "http://34.102.48.89:8080",
    "http://50.217.226.43:80",
    "http://50.217.226.44:80",
    "http://162.223.90.150:80",
    "http://103.75.119.185:80",
    "http://52.73.224.54:3128",
    "http://44.219.175.186:80",
    "http://85.215.64.49:80",
    "http://47.56.110.204:8989",
    "http://68.185.57.66:80",
    "http://158.255.77.168:80",
    "http://195.158.8.123:3128",
    "http://50.174.7.159:80",
    "http://128.199.202.122:8080",
    "http://50.207.199.83:80",
    "http://50.174.7.153:80",
    "http://50.202.75.26:80",
    "http://50.217.226.40:80",
    "http://194.58.24.176:8080",
    "http://54.151.223.88:8080",
    "http://47.128.250.79:8080",
    "http://80.228.235.6:80",
    "http://63.143.57.117:80",
    "http://192.73.244.36:80",
    "http://198.49.68.80:80",
    "http://47.251.43.115:33333",
    "http://50.207.199.86:80",
    "http://211.128.96.206:80",
    "http://8.219.97.248:80",
    "http://203.176.129.85:8080",
    "http://43.153.98.70:13001",
    "http://43.153.2.82:13001",
    "http://154.236.177.102:1977",
    "http://139.59.1.14:80",
    "http://161.35.70.249:8080",
    "http://8.220.204.92:9080",
    "http://133.18.234.13:80",
    "http://165.232.129.150:80",
    "http://43.153.103.91:13001",
    "http://43.153.74.136:13001",
    "http://43.153.21.13:13001",
    "http://23.247.136.248:80",
    "http://3.0.139.128:8080",
    "http://52.221.187.226:8080",
    "http://18.139.108.133:8080",
    "http://3.0.17.193:8080",
    "http://108.136.241.169:8080",
    "http://47.129.1.177:8080",
    "http://81.169.213.169:8888",
    "http://102.23.245.112:8080",
    "http://43.153.14.194:13001",
    "http://23.247.136.254:80",
    "http://43.130.61.237:13001",
    "http://43.153.61.52:13001",
    "http://43.153.88.167:13001",
    "http://2.59.181.248:15200",
    "http://43.153.92.210:13001",
    "http://43.153.107.10:13001",
    "http://43.153.103.42:13001",
    "http://119.156.195.173:3128",
    "http://129.226.155.235:8080",
    "http://87.248.129.26:80",
    "http://72.10.160.171:16413",
    "http://43.153.27.33:13001",
    "http://43.153.43.120:13001",
    "http://43.130.62.137:13001",
    "http://43.153.45.169:13001",  
    # ... (and so on for the rest of your list)
]

def get_proxy():
    if not PROXIES:
        return None
    p = random.choice(PROXIES)
    return {"http": p, "https": p}

def backoff(attempt):
    wait = (2 ** attempt) + random.uniform(0, 1)
    time.sleep(wait)

def throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_request_time = time.time()

def do_request(session, method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        throttle()
        proxy = get_proxy()
        if proxy:
            kwargs.setdefault("proxies", proxy)
        try:
            resp = session.request(method, url, **kwargs)
            if resp.status_code in (200, 201):
                return resp
            if resp.status_code in (429, 503):
                ra = resp.headers.get("Retry-After")
                if ra:
                    time.sleep(float(ra))
                else:
                    backoff(attempt)
            else:
                backoff(attempt)
        except requests.RequestException:
            backoff(attempt)
    raise RuntimeError(f"Failed {method} {url} after {MAX_RETRIES} attempts")

# === Load City Data ===
csv_path = "CitiesToScrape.csv"
if not os.path.exists(csv_path):
    print("⚠️ 'CitiesToScrape.csv' not found. Creating sample data...")
    df_cities = pd.DataFrame([
        {"city": "Tempe", "state": "AZ", "country": "United States", "lat": 33.4255, "lon": -111.94},
        {"city": "Santa Clarita", "state": "CA", "country": "United States", "lat": 34.3917, "lon": -118.5426},
        {"city": "Riverside", "state": "CA", "country": "United States", "lat": 33.9533, "lon": -117.3962}
    ])
else:
    df_cities = pd.read_csv(csv_path)
if NUM_CITIES_TO_TEST:
    df_cities = df_cities.head(NUM_CITIES_TO_TEST)

truck_name_mapping = {
    "Electric High Roof Cargo Van": "van",
    "High Roof Cargo Van": "van",
    "Cargo Van": "van",
    "Panel Van": "van",
    "12 Foot Truck": "12ft_truck",
    "16 Foot Truck": "16ft_truck",
    "16 Foot Cube Van": "16ft_truck",
    "26 Foot Truck": "26ft_truck",
}

lock = threading.Lock()
all_rows = []

def generate_window_name():
    base = ''
    conv = int(time.time() * 1000)
    for _ in range(4):
        base += format(random.randint(0, conv), 'x')
    return 'RENTALWIN' + base

def process_city(row):
    CITY, STATE, COUNTRY = row["city"], row["state"], row["country"]
    lat, lon = row["lat"], row["lon"]
    session = requests.Session()

    # === seed cookies/tokens via homepage GET ===
    home_hdrs = {
        "user-agent":      "Mozilla/5.0",
        "accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua":       '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-platform": '"Windows"'
    }
    do_request(session, "GET", "https://www.pensketruckrental.com/", headers=home_hdrs)

    for lead_time in LEAD_TIMES:
        try:
            pickup  = (datetime.now() + timedelta(days=lead_time)).strftime('%Y-%m-%d')
            dropoff = (datetime.now() + timedelta(days=lead_time+1)).strftime('%Y-%m-%d')
            WN      = generate_window_name()
            CID     = "bbc9ee1c9e934dfa507a8f8e750ef66f"

            sw = random.choice([1366,1440,1536,1600,1680,1920,2048,2560])
            sh = random.choice([768,900,1024,1080,1200,1440,1600])

            hdrs = {
                "user-agent":      home_hdrs["user-agent"],
                "accept":          "application/json, text/plain, */*",
                "accept-language": home_hdrs["accept-language"],
                "origin":          "https://www.pensketruckrental.com",
                "referer":         "https://www.pensketruckrental.com/",
                "x-ibm-client-id": CID,
                "content-type":    "application/json",
                "sec-ch-ua":       home_hdrs["sec-ch-ua"],
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": home_hdrs["sec-ch-ua-platform"],
            }

            print(f"{CITY} ({lead_time}d) — Step 1")
            do_request(session, "POST",
                f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/rule-data"
                f"?cache={int(time.time()*1000)}&window_name={WN}",
                headers=hdrs,
                json={"screenWidth": sw, "screenHeight": sh, "country": COUNTRY}
            )

            print(f"{CITY} ({lead_time}d) — Step 2")
            do_request(session, "GET",
                f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/features/"
                f"customer-profile-activation-switch?cache={int(time.time()*1000)}&window_name={WN}",
                headers=hdrs
            )

            print(f"{CITY} ({lead_time}d) — Step 3")
            do_request(session, "POST",
                f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/location-duration"
                f"?cache={int(time.time()*1000)}&window_name={WN}",
                headers=hdrs,
                json={
                    "country": COUNTRY.lower(),
                    "dropoffLocationSearch": {"address": ""},
                    "pickupLocationSearch": {
                        "latitude": lat, "longitude": lon,
                        "address": f"{CITY}, {STATE}, {COUNTRY}",
                        "city": CITY, "state": STATE, "zip": None
                    },
                    "rentalType": "local",
                    "screenHeight": sh, "screenWidth": sw
                }
            )

            print(f"{CITY} ({lead_time}d) — Step 4")
            do_request(session, "POST",
                f"https://api.pensketruckrental.com/b2b/consumererental/entry/v2/new-quote"
                f"?cache={int(time.time()*1000)}&window_name={WN}",
                headers=hdrs,
                json={"pickupDate": pickup, "dropOffDate": dropoff}
            )

            print(f"{CITY} ({lead_time}d) — Step 5")
            r = do_request(session, "GET",
                f"https://api.pensketruckrental.com/b2b/consumererental/api/v2/quote/summary"
                f"?cache={int(time.time()*1000)}&window_name={WN}",
                headers=hdrs
            )
            data = r.json()

            row = {"City": f"{CITY}, {STATE}", "Lead Time": lead_time, "Pickup Date": pickup}
            for t in data.get("data", {}).get("trucks", []):
                nm = t.get("truckName") or t.get("details", {}).get("description")
                norm = truck_name_mapping.get(nm)
                if not norm or norm == "18 Foot Truck":
                    continue
                row[f"{norm}_dayRate"]  = t.get("dayRate")
                row[f"{norm}_mileRate"] = t.get("mileagePrice")
                row[f"{norm}_bookable"] = (t.get("blockingRules", {}).get("selectable") == "Y")

            with lock:
                all_rows.append(row)
            print(f"✓ {CITY} lead {lead_time} done")

        except Exception as e:
            print(f"❌ {CITY} lead {lead_time} error: {e}")

# === Dispatch ===
df_cities = df_cities.sample(frac=1).reset_index(drop=True)
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_city, r) for _, r in df_cities.iterrows()]
    for f in as_completed(futures):
        if MAX_WORKERS > 1:
            time.sleep(random.uniform(*WAIT_TIME_RANGE))

# === Results ===
df = pd.DataFrame(all_rows)
cols = ["City", "Lead Time", "Pickup Date"] + sorted(c for c in df.columns if c not in ("City","Lead Time","Pickup Date"))
df = df[cols]
pd.set_option("display.max_columns", None)
display(df)
df.to_csv(f"penske_rates_{datetime.now():%Y-%m-%d}.csv", index=False)
