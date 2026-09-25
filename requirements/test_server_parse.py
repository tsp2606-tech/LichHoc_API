import requests
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Login as student or admin
res_login = requests.post("http://127.0.0.1:3001/api/auth/login", json={"email": "ADMIN@gmail.com", "password": "Admin123@"})
assert res_login.status_code == 200, f"Login failed: {res_login.text}"
token = res_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

with open("d:/_Project/LichHoc_Extension/html.txt", "r", encoding="utf-8") as f:
    table1 = f.read()

table2 = table1.replace("21/09/2026 - 27/09/2026", "28/09/2026 - 04/10/2026")
combined = table1 + "\n\n" + table2

# 1. Parse
res_parse = requests.post("http://127.0.0.1:3001/api/schedule/parse", json={"html": combined})
events = res_parse.json().get("events", [])
print(f"Parsed {len(events)} events from HTML.")

# 2. Save
res_save = requests.post("http://127.0.0.1:3001/api/schedule", headers=headers, json={"events": events})
print("Save status:", res_save.status_code)
print("Save response:", res_save.json().get("message"), "count:", res_save.json().get("count"))

# 3. Get
res_get = requests.get("http://127.0.0.1:3001/api/schedule", headers=headers)
print("Get status:", res_get.status_code)
get_events = res_get.json().get("events", [])
print(f"Retrieved {len(get_events)} events from DB:")
weeks = {}
for e in get_events:
    weeks.setdefault(e.get("week_range"), []).append(e)

for w, evs in weeks.items():
    print(f"  Week '{w}': {len(evs)} events")
