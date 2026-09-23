import time
from schedule_api import app, db
from models import User, ScheduleEvent

client = app.test_client()

ts = int(time.time())
student_email = f"student_{ts}@example.com"
admin_email = f"admin_{ts}@example.com"

print("=== 1. TEST POST /api/schedule/parse (Public) ===")
sample_html = """
<table>
  <tr>
    <td>
      <div class="rsApt" title="CS 101 | Nhap Mon Lap Trinh | A101, Co so 1 | 07:00-09:00"></div>
    </td>
    <td>
      <div class="rsApt" title="IS 301 | Co So Du Lieu | Online, Teams | 09:30-11:30"></div>
    </td>
  </tr>
</table>
"""
res = client.post("/api/schedule/parse", json={"html": sample_html})
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
data = res.get_json()
assert data["count"] == 2
assert data["events"][0]["class_code"] == "CS 101"
assert data["events"][0]["day_name"] == "Thứ 2"
assert data["events"][1]["class_code"] == "IS 301"
assert data["events"][1]["day_name"] == "Thứ 3"
print("PASS: Parse HTML works identically to original")

print("\n=== 2. TEST AUTH (Register & Login) ===")
# Register regular user (is_admin=False)
res_reg = client.post("/api/auth/register", json={
    "email": student_email,
    "password": "password123",
    "is_admin": False
})
assert res_reg.status_code == 201, f"Expected 201, got {res_reg.status_code}: {res_reg.get_json()}"

# Register admin user (is_admin=True)
res_admin_reg = client.post("/api/auth/register", json={
    "email": admin_email,
    "password": "adminpassword",
    "is_admin": True
})
assert res_admin_reg.status_code == 201, f"Expected 201, got {res_admin_reg.status_code}"

# Login regular user
res_login = client.post("/api/auth/login", json={
    "email": student_email,
    "password": "password123"
})
assert res_login.status_code == 200
user_token = res_login.get_json()["access_token"]
assert user_token, "No access token returned"
print("PASS: Register & Login returned JWT token")

# Login admin user
res_admin_login = client.post("/api/auth/login", json={
    "email": admin_email,
    "password": "adminpassword"
})
assert res_admin_login.status_code == 200
admin_token = res_admin_login.get_json()["access_token"]
print("PASS: Admin login returned JWT token")

print("\n=== 3. TEST UNAUTHENTICATED ACCESS (401) ===")
res_unauth = client.get("/api/schedule")
assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
print("PASS: Unauthorized request rejected with 401")

print("\n=== 4. TEST POST /api/schedule & GET /api/schedule ===")
headers = {"Authorization": f"Bearer {user_token}"}
res_save = client.post("/api/schedule", headers=headers, json={"html": sample_html})
assert res_save.status_code == 201, f"Expected 201, got {res_save.status_code}: {res_save.get_json()}"
saved_data = res_save.get_json()
assert saved_data["count"] == 2

res_get = client.get("/api/schedule", headers=headers)
assert res_get.status_code == 200
user_schedules = res_get.get_json()
assert user_schedules["count"] == 2
print("PASS: Schedule saved and retrieved for current user")

print("\n=== 5. TEST ADMIN ACCESS (403 FOR REGULAR USER, 200 FOR ADMIN) ===")
res_forbidden = client.get("/admin/dashboard", headers=headers)
assert res_forbidden.status_code == 403, f"Expected 403, got {res_forbidden.status_code}"
print("PASS: Regular user blocked from admin dashboard with 403")

admin_headers = {"Authorization": f"Bearer {admin_token}"}
res_admin = client.get("/admin/dashboard?format=json", headers=admin_headers)
assert res_admin.status_code == 200, f"Expected 200, got {res_admin.status_code}"
admin_data = res_admin.get_json()
assert admin_data["total_users"] >= 2
assert admin_data["total_schedules"] >= 2
print("PASS: Admin dashboard accessible with 200, returns users & schedules")

# Test admin HTML dashboard
res_admin_html = client.get("/admin/dashboard", headers=admin_headers)
assert res_admin_html.status_code == 200
assert "Quản Trị Hệ Thống (Admin Dashboard)" in res_admin_html.get_data(as_text=True)
print("PASS: Admin HTML dashboard rendered successfully")

print("\n=== ALL ACCEPTANCE CRITERIA VERIFIED AND PASSED! ===")
