"""
Schedule Parser & Management API
---------------------------------
Chuyển HTML bảng lịch học (dạng RadScheduler - ASP.NET) sang JSON có cấu trúc,
kết hợp hệ thống xác thực người dùng JWT, lưu trữ database và Admin Dashboard.

Chạy thử:
    python schedule_api.py
"""

import os
import re
from flask import Flask, request, jsonify, render_template_string
from bs4 import BeautifulSoup
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from models import db, User, ScheduleEvent

app = Flask(__name__)

# Cấu hình Database & JWT
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'schedule.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "schedule-jwt-secret-key-super-secure-production-ready-2026-token"
)
app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"]

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()

# Thứ tự các cột trong bảng lịch (điều chỉnh nếu cổng trường bạn khác thứ tự)
DAY_NAMES = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


# ==========================================
# CÁC HÀM PARSER NGUYÊN BẢN (KHÔNG THAY ĐỔI)
# ==========================================
def parse_apt_title(title: str) -> dict:
    """
    Tách chuỗi title dạng:
    'IS 301 E | Cơ Sở Dữ Liệu | P. Online 20, Online | 07:00-09:00'
    thành các trường riêng.
    """
    parts = [p.strip() for p in title.split("|")]
    code = parts[0] if len(parts) > 0 else ""
    subject = parts[1] if len(parts) > 1 else ""
    room_location = parts[2] if len(parts) > 2 else ""
    time_range = parts[3] if len(parts) > 3 else ""

    if "," in room_location:
        room, location = [x.strip() for x in room_location.split(",", 1)]
    else:
        room, location = room_location, ""

    start_time, end_time = "", ""
    m = re.match(r"(\d{2}:\d{2})-(\d{2}:\d{2})", time_range)
    if m:
        start_time, end_time = m.group(1), m.group(2)

    return {
        "class_code": code,
        "subject": subject,
        "room": room,
        "location": location,
        "start_time": start_time,
        "end_time": end_time,
    }


def parse_schedule_html(html: str) -> list:
    """
    Duyệt bảng lịch, tìm mọi <div class="rsApt"> hoặc "rsAptSimple",
    lấy thuộc tính title, kèm số cột (ngày trong tuần) tương ứng.
    """
    soup = BeautifulSoup(html, "html.parser")
    events = []

    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td", recursive=False)
        for col_idx, cell in enumerate(cells):
            apt_divs = cell.find_all("div", class_=lambda c: c and "rsApt" in c.split())
            for apt in apt_divs:
                title = apt.get("title", "").strip()
                if not title:
                    continue
                event = parse_apt_title(title)
                event["day_index"] = col_idx
                event["day_name"] = (
                    DAY_NAMES[col_idx] if col_idx < len(DAY_NAMES) else f"Cột {col_idx}"
                )
                events.append(event)

    return events


# ==========================================
# JWT ERROR HANDLERS (401 Trả về JSON chuẩn)
# ==========================================
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({"error": "Thiếu token xác thực hoặc token không hợp lệ"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify({"error": "Token không hợp lệ"}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token đã hết hạn"}), 401


# ==========================================
# AUTH ENDPOINTS
# ==========================================
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    is_admin = bool(data.get("is_admin", False))

    if not email or not password:
        return jsonify({"error": "Vui lòng cung cấp đầy đủ email và password"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã tồn tại trong hệ thống"}), 400

    new_user = User(email=email, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Đăng ký thành công",
        "user": new_user.to_dict()
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Vui lòng cung cấp đầy đủ email và password"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Email hoặc mật khẩu không chính xác"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin, "email": user.email}
    )

    return jsonify({
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


# ==========================================
# SCHEDULE ENDPOINTS
# ==========================================
@app.route("/api/schedule/parse", methods=["POST"])
def api_parse_schedule():
    """Giữ nguyên hành vi gốc: không yêu cầu auth, trả về {"count", "events"}."""
    data = request.get_json(silent=True) or {}
    html_content = data.get("html", "")
    if not html_content:
        return jsonify({"error": "Thiếu trường 'html' trong body"}), 400

    events = parse_schedule_html(html_content)
    return jsonify({"count": len(events), "events": events})


@app.route("/api/schedule", methods=["POST"])
@jwt_required()
def save_schedule():
    """Lưu các event đã parse gắn với user_id lấy từ JWT token."""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    events_to_save = []

    # Hỗ trợ nhận trực tiếp list events đã parse
    if "events" in data and isinstance(data["events"], list):
        events_to_save = data["events"]
    # Hoặc hỗ trợ gửi html trực tiếp để parse và lưu trong 1 bước
    elif "html" in data and data["html"]:
        events_to_save = parse_schedule_html(data["html"])
    elif isinstance(data, list):
        events_to_save = data
    elif "class_code" in data or "subject" in data:
        events_to_save = [data]
    else:
        return jsonify({"error": "Dữ liệu không hợp lệ. Gửi 'events' (list) hoặc 'html' (str)"}), 400

    saved_records = []
    for ev in events_to_save:
        record = ScheduleEvent(
            user_id=user_id,
            class_code=ev.get("class_code", ""),
            subject=ev.get("subject", ""),
            room=ev.get("room", ""),
            location=ev.get("location", ""),
            start_time=ev.get("start_time", ""),
            end_time=ev.get("end_time", ""),
            day_index=ev.get("day_index", 0),
            day_name=ev.get("day_name", ""),
        )
        db.session.add(record)
        saved_records.append(record)

    db.session.commit()

    return jsonify({
        "message": "Lưu lịch học thành công",
        "count": len(saved_records),
        "events": [r.to_dict() for r in saved_records]
    }), 201


@app.route("/api/schedule", methods=["GET"])
@jwt_required()
def get_user_schedule():
    """Lấy danh sách lịch học của user đang đăng nhập."""
    user_id = int(get_jwt_identity())
    schedules = ScheduleEvent.query.filter_by(user_id=user_id).order_by(ScheduleEvent.day_index).all()
    return jsonify({
        "count": len(schedules),
        "events": [s.to_dict() for s in schedules]
    }), 200


# ==========================================
# ADMIN DASHBOARD & MANAGEMENT ENDPOINTS
# ==========================================
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Admin Dashboard - Quản Lý Lịch Học</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }
    h1 { margin: 0; font-size: 24px; color: #38bdf8; }
    .stats { display: flex; gap: 16px; margin-bottom: 24px; }
    .stat-card { background: #1e293b; padding: 16px 24px; border-radius: 8px; border: 1px solid #334155; flex: 1; }
    .stat-card .num { font-size: 28px; font-weight: bold; color: #f1f5f9; }
    .stat-card .label { font-size: 14px; color: #94a3b8; }
    .user-block { background: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-bottom: 20px; padding: 16px; }
    .user-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .user-title { font-size: 18px; font-weight: 600; color: #e2e8f0; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-admin { background: #dc2626; color: #fff; }
    .badge-user { background: #0284c7; color: #fff; }
    .btn { padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 13px; font-weight: 500; }
    .btn-danger { background: #ef4444; color: white; }
    .btn-danger:hover { background: #dc2626; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #334155; }
    th { background: #0f172a; color: #94a3b8; font-weight: 600; }
    tr:hover { background: #283548; }
    .empty-msg { color: #64748b; font-style: italic; padding: 8px 0; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🛡️ Quản Trị Hệ Thống (Admin Dashboard)</h1>
      <div>Đăng nhập với tư cách: <strong>{{ current_admin_email }}</strong></div>
    </div>

    <div class="stats">
      <div class="stat-card">
        <div class="num">{{ total_users }}</div>
        <div class="label">Tổng số Người Dùng</div>
      </div>
      <div class="stat-card">
        <div class="num">{{ total_schedules }}</div>
        <div class="label">Tổng số Tiết / Lịch Học Đã Lưu</div>
      </div>
    </div>

    <h2>Danh Sách Người Dùng & Lịch Học</h2>
    {% for user in users %}
      <div class="user-block">
        <div class="user-header">
          <div class="user-title">
            #{{ user.id }} - {{ user.email }}
            {% if user.is_admin %}
              <span class="badge badge-admin">Admin</span>
            {% else %}
              <span class="badge badge-user">User</span>
            {% endif %}
            <span style="font-size: 13px; color: #94a3b8; margin-left: 12px;">Ngày tạo: {{ user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else '' }}</span>
          </div>
          <div>
            <button class="btn btn-danger" onclick="deleteUser({{ user.id }})">Xóa User</button>
          </div>
        </div>

        {% if user.schedules %}
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Thứ</th>
                <th>Mã Lớp</th>
                <th>Tên Môn Học</th>
                <th>Phòng</th>
                <th>Địa Điểm</th>
                <th>Thời Gian</th>
                <th>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {% for s in user.schedules %}
                <tr>
                  <td>{{ s.id }}</td>
                  <td><strong>{{ s.day_name }}</strong></td>
                  <td>{{ s.class_code }}</td>
                  <td>{{ s.subject }}</td>
                  <td>{{ s.room }}</td>
                  <td>{{ s.location }}</td>
                  <td>{{ s.start_time }} - {{ s.end_time }}</td>
                  <td>
                    <button class="btn btn-danger" style="padding: 4px 8px; font-size: 12px;" onclick="deleteSchedule({{ s.id }})">Xóa</button>
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <div class="empty-msg">Chưa có dữ liệu lịch học nào được lưu.</div>
        {% endif %}
      </div>
    {% endfor %}
  </div>

  <script>
    const token = new URLSearchParams(window.location.search).get('token') || '';
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    async function deleteSchedule(id) {
      if (!confirm('Bạn có chắc muốn xóa lịch học ID ' + id + '?')) return;
      const res = await fetch('/admin/schedule/' + id + (token ? '?token=' + token : ''), {
        method: 'DELETE',
        headers: headers
      });
      if (res.ok) {
        alert('Đã xóa thành công!');
        window.location.reload();
      } else {
        const err = await res.json();
        alert('Lỗi: ' + (err.error || 'Không thể xóa'));
      }
    }

    async function deleteUser(id) {
      if (!confirm('Bạn có chắc muốn xóa toàn bộ tài khoản và lịch học của User ID ' + id + '?')) return;
      const res = await fetch('/admin/user/' + id + (token ? '?token=' + token : ''), {
        method: 'DELETE',
        headers: headers
      });
      if (res.ok) {
        alert('Đã xóa user thành công!');
        window.location.reload();
      } else {
        const err = await res.json();
        alert('Lỗi: ' + (err.error || 'Không thể xóa'));
      }
    }
  </script>
</body>
</html>
"""


@app.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    """Dashboard quản trị hệ thống - Chỉ Admin mới có quyền truy cập."""
    claims = get_jwt()
    is_admin = claims.get("is_admin", False)

    # Kiểm tra thêm trong DB nếu claims chưa cập nhật
    if not is_admin:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if user and user.is_admin:
            is_admin = True

    if not is_admin:
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    users = User.query.order_by(User.id).all()
    total_users = len(users)
    total_schedules = ScheduleEvent.query.count()

    # Trả về JSON nếu client yêu cầu JSON hoặc định dạng format=json
    if request.is_json or request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify({
            "total_users": total_users,
            "total_schedules": total_schedules,
            "users": [
                {
                    **u.to_dict(),
                    "schedules": [s.to_dict() for s in u.schedules]
                }
                for u in users
            ]
        }), 200

    admin_email = claims.get("email", "Admin")
    return render_template_string(
        ADMIN_DASHBOARD_TEMPLATE,
        users=users,
        total_users=total_users,
        total_schedules=total_schedules,
        current_admin_email=admin_email
    )


@app.route("/admin/schedule/<int:event_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_schedule(event_id: int):
    """Admin xóa 1 bản ghi lịch học cụ thể."""
    claims = get_jwt()
    if not claims.get("is_admin", False):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    event = ScheduleEvent.query.get(event_id)
    if not event:
        return jsonify({"error": "Không tìm thấy lịch học cần xóa"}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Đã xóa lịch học thành công", "deleted_id": event_id}), 200


@app.route("/admin/user/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id: int):
    """Admin xóa 1 user và toàn bộ lịch học liên quan."""
    claims = get_jwt()
    if not claims.get("is_admin", False):
        curr_id = int(get_jwt_identity())
        user = User.query.get(curr_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"error": "Không tìm thấy người dùng cần xóa"}), 404

    db.session.delete(target_user)
    db.session.commit()
    return jsonify({"message": "Đã xóa người dùng thành công", "deleted_user_id": user_id}), 200


@app.route("/api/schedule/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
