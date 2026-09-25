import sys
sys.stdout.reconfigure(encoding='utf-8')
from schedule_api import parse_schedule_html

# Read the raw text from user prompt
with open("test_prompt_html.html", "r", encoding="utf-8") as f:
    html = f.read()

events = parse_schedule_html(html)
print(f"Total events parsed: {len(events)}")
weeks = {}
for e in events:
    w = e.get("week_range", "")
    weeks.setdefault(w, []).append(e)

for w, evs in weeks.items():
    print(f"Week '{w}': {len(evs)} events")
    for ev in evs:
        print(f"   day {ev['day_index']} ({ev['day_name']}): {ev['class_code']} | {ev['start_time']}-{ev['end_time']}")
