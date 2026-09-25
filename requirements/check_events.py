import sys
sys.stdout.reconfigure(encoding='utf-8')
from schedule_api import app, db
from models import ScheduleEvent, User

with app.app_context():
    evs = ScheduleEvent.query.all()
    print(f"Total events in ScheduleEvent table: {len(evs)}")
    by_user = {}
    for e in evs:
        by_user.setdefault(e.user_id, []).append(e)

    for uid, user_evs in by_user.items():
        u = User.query.get(uid)
        print(f"\nUser {uid} ({u.email if u else 'Unknown'}): {len(user_evs)} events")
        for e in user_evs:
            print(f"  id={e.id} | week='{e.week_range}' | day={e.day_index} ({e.day_name}) | time={e.start_time}-{e.end_time} | {e.class_code} | {e.subject}")
