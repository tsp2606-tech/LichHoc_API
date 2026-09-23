import json
from bs4 import BeautifulSoup
from schedule_api import parse_apt_title, DAY_NAMES

html = open('html.txt', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

content_table = soup.find('table', class_='rsContentTable') or soup
rows = content_table.find_all('tr')

events = []
for row in rows:
    cells = row.find_all('td', recursive=False)
    if len(cells) < 7:
        continue
    for col_idx, cell in enumerate(cells):
        apt_divs = cell.find_all('div', class_=lambda c: c and 'rsApt' in c.split())
        for apt in apt_divs:
            title = apt.get('title', '').strip()
            if not title:
                continue
            event = parse_apt_title(title)
            event['day_index'] = col_idx
            event['day_name'] = DAY_NAMES[col_idx]
            # Extra styling info from the HTML (e.g., color for online vs offline)
            style = apt.get('style', '')
            event['is_online'] = 'online' in event['room'].lower() or 'online' in event['location'].lower() or '#c0ffc0' in style.lower()
            events.append(event)

with open('clean_events.json', 'w', encoding='utf-8') as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Exported {len(events)} events to clean_events.json")
