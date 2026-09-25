import sys
sys.stdout.reconfigure(encoding='utf-8')
from schedule_api import parse_schedule_html

# Let's read the exact content of user request
html_sample = """<div class="main-border-center">
                    <div id="ctl00_PlaceHolderContentArea_ctl00_RightZone" class="column2" style="width:100%;">
                    <h2>
							21/09/2026 - 27/09/2026
						</h2>
					</div><div class="rsContent rsWeekView">
									<table class="rsContentTable" cellpadding="0" cellspacing="0" border="0" style="width:100%;">
										<tbody><tr style="height:15px;">
											<td><div class="rsWrap" style="z-index:64;">
												<div id="ctl00_PlaceHolderContentArea_ctl00_ctl01_RadScheduler1_86_0" title="IS 301 E | Cơ Sở Dữ Liệu | P. Online 20, Online | 07:00-09:00" class="rsApt rsAptSimple" style="background-color:#C0FFC0;height:116px;width:90%;left:0%;">
												</div>
											</div></td>
										</tr>
									</tbody></table>
					</div>
</div>

<div class="main-border-center">
                    <div id="ctl00_PlaceHolderContentArea_ctl00_RightZone" class="column2" style="width:100%;">
                    <h2>
					28/09/2026 - 04/10/2026
				</h2>
			</div><div class="rsContent rsWeekView">
							<table class="rsContentTable" cellpadding="0" cellspacing="0" border="0" style="width:100%;">
								<tbody><tr style="height:15px;">
									<td><div class="rsWrap" style="z-index:64;">
										<div id="ctl00_PlaceHolderContentArea_ctl00_ctl01_RadScheduler1_88_0" title="IS 301 E | Cơ Sở Dữ Liệu | P. Online 20, Online | 07:00-09:00" class="rsApt rsAptSimple" style="background-color:#C0FFC0;height:116px;width:90%;left:0%;">
										</div>
									</div></td>
								</tr>
							</tbody></table>
			</div>
</div>"""

evs = parse_schedule_html(html_sample)
print(f"Parsed {len(evs)} events:")
for e in evs:
    print(f"  week_range: '{e.get('week_range')}' | {e.get('class_code')}")
