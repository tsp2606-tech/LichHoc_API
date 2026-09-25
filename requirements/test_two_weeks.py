import requests
import json
from schedule_api import app, parse_schedule_html

user_html = """
<div class="main-border-center">
    <div id="ctl00_PlaceHolderContentArea_ctl00_RightZone" class="column2" style="width:100%;">
        <div id="ctl00_PlaceHolderContentArea_ctl00_ctl01_RadScheduler1" class="RadScheduler RadScheduler_Sitefinity">
            <div class="rsTopWrap">
                <div class="rsHeader">
                    <h2>21/09/2026 - 27/09/2026</h2>
                </div>
                <div class="rsContent rsWeekView">
                    <table class="rsContentTable">
                        <tbody>
                            <tr>
                                <td>
                                    <div class="rsApt rsAptSimple" title="IS 301 E | Cơ Sở Dữ Liệu | P. Online 20, Online | 07:00-09:00"></div>
                                </td>
                                <td>
                                    <div class="rsApt" title="CS 311 Q | Lập Trình Hướng Đối Tượng | P. 308, Hòa Khánh Nam - Tòa Nhà G | 07:00-09:00"></div>
                                </td>
                                <td>
                                    <div class="rsApt" title="IS 301 E | Cơ Sở Dữ Liệu | P. 308, 78A Phan Văn Trị | 07:00-09:00"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="PHY 101 K3 | Vật Lý Đại Cương 1 | P. 305, K7/25 Quang Trung | 07:00-11:15"></div>
                                </td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td><td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="CS 297 E | Đồ Án CDIO | P. 403, 78A Phan Văn Trị | 09:15-11:15"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="rsApt" title="DS 103 CA | Các Ứng Dụng AI (Artificial Intelligence) Cơ Bản | P. 308, 209 Phan Thanh | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td>
                                <td>
                                    <div class="rsApt rsAptSimple" title="PHY 101 K | Vật Lý Đại Cương 1 | P. Online 6, Online | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="PHY 101 K | Vật Lý Đại Cương 1 | P. 408, 209 Phan Thanh | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="ES 221 AC | Bóng Đá Sơ Cấp | P. Sân thể thao 2, Hòa Khánh Nam - Tòa Nhà A | 14:00-16:15"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="main-border-center">
    <div id="ctl00_PlaceHolderContentArea_ctl00_RightZone" class="column2" style="width:100%;">
        <div id="ctl00_PlaceHolderContentArea_ctl00_ctl01_RadScheduler1" class="RadScheduler RadScheduler_Sitefinity">
            <div class="rsTopWrap">
                <div class="rsHeader">
                    <h2>28/09/2026 - 04/10/2026</h2>
                </div>
                <div class="rsContent rsWeekView">
                    <table class="rsContentTable">
                        <tbody>
                            <tr>
                                <td>
                                    <div class="rsApt rsAptSimple" title="IS 301 E | Cơ Sở Dữ Liệu | P. Online 20, Online | 07:00-09:00"></div>
                                </td>
                                <td>
                                    <div class="rsApt" title="CS 311 Q | Lập Trình Hướng Đối Tượng | P. 308, Hòa Khánh Nam - Tòa Nhà G | 07:00-09:00"></div>
                                </td>
                                <td>
                                    <div class="rsApt" title="IS 301 E | Cơ Sở Dữ Liệu | P. 308, 78A Phan Văn Trị | 07:00-09:00"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="rsApt rsAptSimple" title="DS 103 CA | Các Ứng Dụng AI (Artificial Intelligence) Cơ Bản | P. Online 44, Online | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td>
                                <td>
                                    <div class="rsApt rsAptSimple" title="PHY 101 K | Vật Lý Đại Cương 1 | P. Online 6, Online | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="PHY 101 K | Vật Lý Đại Cương 1 | P. 408, 209 Phan Thanh | 13:00-15:00"></div>
                                </td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="ES 221 AC | Bóng Đá Sơ Cấp | P. Sân thể thao 2, Hòa Khánh Nam - Tòa Nhà A | 14:00-16:15"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>
                                    <div class="rsApt" title="CS 297 E | Đồ Án CDIO | P. 408, Hòa Khánh Nam - Tòa Nhà G | 17:45-21:00"></div>
                                </td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
"""

events = parse_schedule_html(user_html)
print(f"Total events parsed: {len(events)}")
week1_events = [e for e in events if e.get("week_range") == "21/09/2026 - 27/09/2026"]
week2_events = [e for e in events if e.get("week_range") == "28/09/2026 - 04/10/2026"]

import sys
sys.stdout.reconfigure(encoding='utf-8')

print(f"Week 1 events: {len(week1_events)}")
for e in week1_events:
    print(f"  [W1] Day {e['day_index']} ({e['day_name']}): {e['class_code']} | {e['start_time']}-{e['end_time']} | {e['room']}")

print(f"Week 2 events: {len(week2_events)}")
for e in week2_events:
    print(f"  [W2] Day {e['day_index']} ({e['day_name']}): {e['class_code']} | {e['start_time']}-{e['end_time']} | {e['room']}")

assert len(week1_events) == 9, f"Expected 9 events in week 1, got {len(week1_events)}"
assert len(week2_events) == 8, f"Expected 8 events in week 2, got {len(week2_events)}"

# Check specific differences
w1_sun = [e for e in week1_events if e["day_index"] == 6]
w2_sun = [e for e in week2_events if e["day_index"] == 6]
assert len(w1_sun) == 1 and w1_sun[0]["class_code"] == "PHY 101 K3", "Week 1 must have PHY 101 K3 on Sunday"
assert len(w2_sun) == 0, "Week 2 must have no classes on Sunday"

w1_tue_evening = [e for e in week1_events if e["day_index"] == 1 and e["start_time"] == "17:45"]
w2_tue_evening = [e for e in week2_events if e["day_index"] == 1 and e["start_time"] == "17:45"]
assert len(w1_tue_evening) == 0, "Week 1 must NOT have Tuesday evening CS 297 E"
assert len(w2_tue_evening) == 1 and w2_tue_evening[0]["class_code"] == "CS 297 E", "Week 2 MUST have Tuesday evening CS 297 E"

print("\nALL ASSERTIONS PASSED! 2 weeks correctly separated with accurate week_range.")
