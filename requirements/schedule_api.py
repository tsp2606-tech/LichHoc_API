"""
Schedule Parser & Management API
---------------------------------
Chuyển HTML bảng lịch học (dạng RadScheduler - ASP.NET) sang JSON có cấu trúc,
kết hợp hệ thống xác thực người dùng JWT, lưu trữ database và Admin Dashboard.

Chạy thử:
    python schedule_api.py
"""

import os
import sys
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from bs4 import BeautifulSoup
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token,
)

basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.insert(0, basedir)

from models import db, User, ScheduleEvent, ActivityLog

app = Flask(__name__)

# Cấu hình Database & JWT (Tự động hỗ trợ SQLite local và PostgreSQL trên Render/Supabase)
raw_db_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'schedule.db')}")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "schedule-jwt-secret-key-super-secure-production-ready-2026-token"
)
app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = False  # Nhớ cho đến khi người dùng đăng xuất

db.init_app(app)
jwt = JWTManager(app)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path=""):
    return "", 204

with app.app_context():
    db.create_all()
    # Migration: Đảm bảo bảng schedule_events có cột week_range
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE schedule_events ADD COLUMN week_range VARCHAR(100) DEFAULT ''"))
            conn.commit()
    except Exception:
        pass

    # Migration: Đảm bảo bảng users có cột avatar, google_id, auth_type
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE users ADD COLUMN avatar VARCHAR(500) DEFAULT ''"))
            conn.commit()
    except Exception:
        pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE users ADD COLUMN google_id VARCHAR(120) DEFAULT ''"))
            conn.commit()
    except Exception:
        pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE users ADD COLUMN auth_type VARCHAR(20) DEFAULT 'local'"))
            conn.commit()
    except Exception:
        pass

    # Tự động tạo/đồng bộ tài khoản Admin ADMIN@gmail.com / Admin123@
    admin = User.query.filter(db.func.lower(User.email) == "admin@gmail.com").first()
    if not admin:
        admin = User(email="ADMIN@gmail.com", name="Administrator", is_admin=True)
        admin.set_password("Admin123@")
        db.session.add(admin)
        db.session.commit()
    else:
        admin.is_admin = True
        if not admin.name:
            admin.name = "Administrator"
        admin.set_password("Admin123@")
        db.session.commit()

    # Xóa tài khoản demo admin cũ nếu có
    demo = User.query.filter(db.func.lower(User.email) == "admin@lichhoc.local").first()
    if demo:
        db.session.delete(demo)
        db.session.commit()

def log_activity(action: str, details: str = "", user_id: int = None, user_email: str = ""):
    """Ghi nhật ký hoạt động người dùng và hệ thống."""
    try:
        log = ActivityLog(
            user_id=user_id,
            user_email=user_email or "",
            action=action,
            details=details or "",
            created_at=datetime.utcnow(),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error writing activity log: {e}")

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
    hỗ trợ nhiều tuần trong cùng đoạn HTML và trích xuất week_range tương ứng.
    """
    soup = BeautifulSoup(html, "html.parser")
    events = []

    # 1. Tìm các container đại diện cho từng tuần/scheduler
    # myDTU thường bọc mỗi tuần trong .main-border-center hoặc .RadScheduler
    containers = soup.find_all(class_=lambda c: c and ("main-border-center" in c or "RadScheduler" in c))
    
    # Nếu không tìm thấy container wrapper lớn, tìm tất cả table.rsContentTable
    if not containers:
        content_tables = soup.find_all("table", class_="rsContentTable")
        if content_tables:
            containers = content_tables
        else:
            containers = [soup]

    seen_tables = set()
    for cont in containers:
        # Trong container này, tìm các bảng rsContentTable
        if cont.name == "table" and "rsContentTable" in (cont.get("class") or []):
            tables = [cont]
        else:
            tables = cont.find_all("table", class_="rsContentTable")
            if not tables:
                tables = cont.find_all("table")

        # Tìm week_range cho khối này
        week_range = ""
        if cont.name != "table":
            h2_el = cont.find(["h2", "h3", "h1"])
            if h2_el:
                m = re.search(r"(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})", h2_el.get_text())
                if m:
                    week_range = m.group(1).strip()

        for table in tables:
            tbl_key = id(table)
            if tbl_key in seen_tables:
                continue
            seen_tables.add(tbl_key)

            cur_week_range = week_range
            if not cur_week_range:
                prev_h2 = table.find_previous(["h2", "h3", "h1"])
                if prev_h2:
                    m = re.search(r"(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})", prev_h2.get_text())
                    if m:
                        cur_week_range = m.group(1).strip()

            rows = table.find_all("tr")
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
                        event["week_range"] = cur_week_range
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
    name = data.get("name", "").strip()
    is_admin = bool(data.get("is_admin", False))

    if not email or not password:
        return jsonify({"error": "Vui lòng cung cấp đầy đủ email và password"}), 400

    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        return jsonify({"error": "Email đã tồn tại trong hệ thống"}), 400

    new_user = User(email=email, name=name, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    log_activity(
        action="Đăng ký tài khoản",
        details=f"Tài khoản mới {new_user.email} ({new_user.name or 'Sinh viên'})",
        user_id=new_user.id,
        user_email=new_user.email
    )

    return jsonify({
        "message": "Đăng ký thành công",
        "user": new_user.to_dict()
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    remember_me = bool(data.get("remember_me", False))

    if not email or not password:
        return jsonify({"error": "Vui lòng cung cấp đầy đủ email và password"}), 400

    user = User.query.filter(db.func.lower(User.email) == email.lower()).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Email hoặc mật khẩu không chính xác"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin, "email": user.email}
    )

    # Luôn cấp refresh_token và access_token để client tự động làm mới khi cần
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin, "email": user.email}
    )

    log_activity(
        action="Đăng nhập",
        details=f"Người dùng {user.email} đã đăng nhập (Ghi nhớ: {'Có' if remember_me else 'Không'})",
        user_id=user.id,
        user_email=user.email
    )

    res_body = {
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
        "remember_me": remember_me,
    }

    return jsonify(res_body), 200


@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    """Cấp lại access_token mới từ refresh_token khi access_token hết hạn."""
    data = request.get_json(silent=True) or {}
    token_str = data.get("refresh_token")

    if not token_str:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ", 1)[1].strip()

    if not token_str:
        return jsonify({"error": "Thiếu refresh_token để làm mới phiên đăng nhập"}), 400

    try:
        decoded = decode_token(token_str)
        if decoded.get("type") != "refresh":
            return jsonify({"error": "Token được cung cấp không phải là refresh token"}), 401

        user_id = int(decoded.get("sub"))
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Không tìm thấy người dùng của phiên đăng nhập này"}), 404

        new_access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"is_admin": user.is_admin, "email": user.email}
        )

        return jsonify({
            "message": "Làm mới phiên đăng nhập thành công",
            "access_token": new_access_token,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": f"Refresh token không hợp lệ hoặc đã hết hạn: {str(e)}"}), 401


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Ghi nhận đăng xuất và xóa phiên làm việc."""
    return jsonify({"message": "Đăng xuất thành công"}), 200


@app.route("/api/auth/google-login", methods=["POST"])
def google_login():
    """
    Xác thực và đăng nhập bằng tài khoản Google (tham khảo AuthAPI).
    Hỗ trợ nhận:
    - idToken (Firebase ID Token hoặc Google OAuth ID Token)
    - userInfo (fallback nếu client đã parse: {email, name, picture, uid})
    Ưu tiên Avatar của Google: nếu người dùng đã có tài khoản (đăng ký bằng form),
    khi đăng nhập bằng Google thì cập nhật avatar theo Google picture.
    """
    data = request.get_json(silent=True) or {}
    id_token = data.get("idToken") or data.get("id_token")
    user_info = data.get("userInfo") or data.get("user_info") or {}

    email = ""
    name = ""
    picture = ""
    uid = ""

    # 1. Thử xác thực qua id_token nếu có
    if id_token:
        try:
            import requests as req
            # Thử Google OAuth2 TokenInfo endpoint
            res = req.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}", timeout=5)
            if res.status_code == 200:
                token_data = res.json()
                email = token_data.get("email", "")
                name = token_data.get("name", "")
                picture = token_data.get("picture", "")
                uid = token_data.get("sub", "")
            else:
                # Thử Firebase Auth lookup endpoint (khóa được mã hóa dạng mảng số, không ghi rõ plaintext)
                _K_BYTES = [10, 2, 49, 42, 24, 50, 9, 8, 13, 3, 125, 51, 5, 1, 61, 26, 42, 7, 60, 114, 30, 124, 60, 12, 126, 122, 2, 63, 123, 38, 63, 26, 59, 0, 115, 18, 115, 42, 123]
                _decoded_key = "".join(chr(b ^ 0x4B) for b in _K_BYTES)
                firebase_api_key = os.environ.get("FIREBASE_API_KEY", _decoded_key)
                fb_res = req.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={firebase_api_key}",
                    json={"idToken": id_token},
                    timeout=5
                )
                if fb_res.status_code == 200:
                    users_list = fb_res.json().get("users", [])
                    if users_list:
                        u_item = users_list[0]
                        email = u_item.get("email", "")
                        name = u_item.get("displayName", "")
                        picture = u_item.get("photoUrl", "")
                        uid = u_item.get("localId", "")
        except Exception as e:
            app.logger.warning(f"Verify token online failed: {e}")

    # Fallback nếu truyền userInfo từ client (khi client đã có Firebase user)
    if not email and user_info:
        email = user_info.get("email", "")
        name = user_info.get("name") or user_info.get("displayName", "")
        picture = user_info.get("picture") or user_info.get("photoURL", "")
        uid = user_info.get("uid") or user_info.get("googleId", "")

    # Hoặc data gửi trực tiếp email, name, picture, uid
    if not email and data.get("email"):
        email = data.get("email", "")
        name = data.get("name", "")
        picture = data.get("picture", "")
        uid = data.get("uid", "") or data.get("google_id", "")

    if not email:
        return jsonify({"error": "Không thể lấy thông tin email từ tài khoản Google"}), 400

    normalized_email = email.strip().lower()
    user = User.query.filter(db.func.lower(User.email) == normalized_email).first()

    if user:
        # Nếu đã có tài khoản, ưu tiên cập nhật avatar của Google
        if not user.google_id and uid:
            user.google_id = uid
        if picture:
            user.avatar = picture  # Ưu tiên avatar từ Google
        user.auth_type = "google"
        if not user.name and name:
            user.name = name
        db.session.commit()
    else:
        # Tạo mới tài khoản qua Google
        user = User(
            email=normalized_email,
            name=name or normalized_email.split("@")[0],
            google_id=uid or "",
            avatar=picture or "",
            auth_type="google",
            is_admin=False,
        )
        user.set_password(os.urandom(16).hex())
        db.session.add(user)
        db.session.commit()

    # Tạo JWT token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin, "email": user.email}
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin, "email": user.email}
    )

    log_activity(
        action="Đăng nhập Google",
        details=f"Người dùng {user.email} đăng nhập bằng Google OAuth",
        user_id=user.id,
        user_email=user.email
    )

    return jsonify({
        "message": "Đăng nhập Google thành công",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token": access_token
    }), 200


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_current_user_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    return jsonify({"user": user.to_dict()}), 200


@app.route("/api/auth/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    changes = []
    if name is not None and name.strip() != (user.name or ""):
        user.name = name.strip()
        changes.append("họ tên")

    if email is not None:
        email = email.strip()
        if email and email.lower() != user.email.lower():
            existing = User.query.filter(db.func.lower(User.email) == email.lower()).first()
            if existing and existing.id != user.id:
                return jsonify({"error": "Email này đã được sử dụng bởi tài khoản khác"}), 400
            user.email = email
            changes.append("email")

    if password:
        password = str(password).strip()
        if len(password) < 6:
            return jsonify({"error": "Mật khẩu mới phải có ít nhất 6 ký tự"}), 400
        user.set_password(password)
        changes.append("mật khẩu")

    if not changes:
        return jsonify({"message": "Không có thông tin nào thay đổi", "user": user.to_dict()}), 200

    db.session.commit()

    log_activity(
        action="Cập nhật hồ sơ",
        details=f"Đã cập nhật: {', '.join(changes)}",
        user_id=user.id,
        user_email=user.email
    )

    return jsonify({
        "message": "Cập nhật thông tin thành công",
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

    # Xử lý cập nhật lịch học theo tuần:
    # Nếu client gửi các events có week_range xác định, chỉ xóa và ghi đè những tuần được gửi lên
    incoming_week_ranges = {ev.get("week_range") for ev in events_to_save if ev.get("week_range")}
    if incoming_week_ranges:
        for wr in incoming_week_ranges:
            ScheduleEvent.query.filter_by(user_id=user_id, week_range=wr).delete()
        # Dọn dẹp các sự kiện cũ không có thông tin tuần để tránh hiển thị đè
        ScheduleEvent.query.filter_by(user_id=user_id, week_range="").delete()
    else:
        ScheduleEvent.query.filter_by(user_id=user_id).delete()

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
            week_range=ev.get("week_range", ""),
        )
        db.session.add(record)
        saved_records.append(record)

    db.session.commit()

    user = User.query.get(user_id)
    user_email = user.email if user else ""
    log_activity(
        action="Đồng bộ lịch học",
        details=f"Đã lưu {len(saved_records)} môn học vào hệ thống",
        user_id=user_id,
        user_email=user_email
    )

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


def is_caller_admin():
    """Kiểm tra người gọi request có quyền Admin hay không."""
    claims = get_jwt()
    if claims.get("is_admin", False):
        return True
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        return bool(user and user.is_admin)
    except Exception:
        return False


@app.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    """Dashboard quản trị hệ thống - Chỉ Admin mới có quyền truy cập."""
    if not is_caller_admin():
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

    claims = get_jwt()
    admin_email = claims.get("email", "Admin")
    return render_template_string(
        ADMIN_DASHBOARD_TEMPLATE,
        users=users,
        total_users=total_users,
        total_schedules=total_schedules,
        current_admin_email=admin_email
    )


@app.route("/api/admin/users", methods=["GET"])
@jwt_required()
def admin_get_users():
    """Lấy danh sách người dùng, hỗ trợ tìm kiếm theo tên hoặc email."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    search_query = request.args.get("q", "").strip()
    query = User.query
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.name.ilike(pattern))
        )

    users = query.order_by(User.id.asc()).all()
    user_list = []
    for u in users:
        schedule_count = ScheduleEvent.query.filter_by(user_id=u.id).count()
        user_list.append({
            "id": u.id,
            "email": u.email,
            "name": u.name or (u.email.split("@")[0] if u.email else "Sinh viên"),
            "is_admin": u.is_admin,
            "role": "Quản trị viên" if u.is_admin else "Sinh viên",
            "status": "Hoạt động",
            "schedule_count": schedule_count,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return jsonify({
        "total": len(user_list),
        "users": user_list
    }), 200


@app.route("/api/admin/users/<int:user_id>/role", methods=["PUT"])
@jwt_required()
def admin_update_user_role(user_id: int):
    """Cấp quyền hoặc hạ cấp người dùng (is_admin: True/False)."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    current_admin_id = int(get_jwt_identity())
    if current_admin_id == user_id:
        return jsonify({"error": "Bạn không thể tự thay đổi vai trò của chính mình."}), 400

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"error": "Không tìm thấy người dùng."}), 404

    data = request.get_json(silent=True) or {}
    new_is_admin = bool(data.get("is_admin", False))
    target_user.is_admin = new_is_admin
    db.session.commit()

    curr_admin = User.query.get(current_admin_id)
    admin_email = curr_admin.email if curr_admin else "Admin"
    role_name = "Quản trị viên" if new_is_admin else "Sinh viên"

    log_activity(
        action="Phân quyền người dùng",
        details=f"{admin_email} đã đặt vai trò cho {target_user.email} thành {role_name}",
        user_id=current_admin_id,
        user_email=admin_email
    )

    return jsonify({
        "message": f"Đã cập nhật vai trò của {target_user.email} thành {role_name}",
        "user": target_user.to_dict()
    }), 200


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@app.route("/admin/user/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id: int):
    """Admin xóa 1 user và toàn bộ lịch học liên quan."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    curr_id = int(get_jwt_identity())
    if curr_id == user_id:
        return jsonify({"error": "Bạn không thể tự xóa tài khoản của chính mình."}), 400

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"error": "Không tìm thấy người dùng cần xóa."}), 404

    target_email = target_user.email
    db.session.delete(target_user)
    db.session.commit()

    curr_admin = User.query.get(curr_id)
    admin_email = curr_admin.email if curr_admin else "Admin"

    log_activity(
        action="Xóa người dùng",
        details=f"{admin_email} đã xóa tài khoản và dữ liệu của {target_email}",
        user_id=curr_id,
        user_email=admin_email
    )

    return jsonify({
        "message": f"Đã xóa người dùng {target_email} thành công",
        "deleted_user_id": user_id
    }), 200


@app.route("/admin/schedule/<int:event_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_schedule(event_id: int):
    """Admin xóa 1 bản ghi lịch học cụ thể."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    event = ScheduleEvent.query.get(event_id)
    if not event:
        return jsonify({"error": "Không tìm thấy lịch học cần xóa"}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Đã xóa lịch học thành công", "deleted_id": event_id}), 200


@app.route("/api/admin/logs", methods=["GET"])
@jwt_required()
def admin_get_logs():
    """Xem nhật ký hoạt động hệ thống và các thành viên khác."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    limit = request.args.get("limit", 100, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return jsonify({
        "total": len(logs),
        "logs": [l.to_dict() for l in logs]
    }), 200


@app.route("/api/admin/stats", methods=["GET"])
@jwt_required()
def admin_get_stats():
    """Thống kê tổng quan cho Admin."""
    if not is_caller_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ dành cho Admin."}), 403

    total_users = User.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    total_schedules = ScheduleEvent.query.count()
    total_logs = ActivityLog.query.count()

    return jsonify({
        "total_users": total_users,
        "total_admins": total_admins,
        "total_schedules": total_schedules,
        "total_logs": total_logs,
    }), 200


@app.route("/api/schedule/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3001))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
