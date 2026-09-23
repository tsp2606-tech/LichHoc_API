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
            events.append(event)

print(f"Correct unique events count: {len(events)}")
for e in events:
    print(f"{e['day_name']} ({e['start_time']} - {e['end_time']}): {e['class_code']} | {e['subject']} | {e['room']} ({e['location']})")
