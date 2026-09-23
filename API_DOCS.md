# CRUD LichHoc API Documentation

Tài liệu này cung cấp thông tin chi tiết về tất cả các API routes, payload, và response của dịch vụ Quản lý Lịch Học (CRUD LichHoc API) để Frontend có thể dễ dàng tích hợp.

- **Base URL:** `http://localhost:5000`
- **Swagger Docs:** `http://localhost:5000/api-docs`

---

## 1. Lấy danh sách tất cả lịch học
- **Route:** `GET /api/lich-hoc`
- **Mô tả:** Trả về danh sách tất cả các lịch học trong cơ sở dữ liệu (được sắp xếp theo thời gian tạo mới nhất).
- **Payload (Request Body):** *Không có*
- **Response (200 OK):**
```json
[
  {
    "_id": "66b437c9ce982033cd76a63",
    "monHoc": "Lập trình Web",
    "giangVien": "ThS. Nguyễn Văn A",
    "phongHoc": "A101",
    "thu": "Thứ Hai",
    "tietBatDau": 1,
    "tietKetThuc": 3,
    "thoiGian": "07:00 - 09:30",
    "ghiChu": "Mang theo laptop",
    "createdAt": "2026-09-23T10:00:00.000Z",
    "updatedAt": "2026-09-23T10:00:00.000Z"
  }
]
```

---

## 2. Thêm lịch học mới
- **Route:** `POST /api/lich-hoc`
- **Mô tả:** Tạo một bản ghi lịch học mới trong cơ sở dữ liệu. `monHoc` và `thu` là các trường bắt buộc.
- **Payload (Request Body):**
```json
{
  "monHoc": "Lập trình Web",
  "giangVien": "ThS. Nguyễn Văn A",
  "phongHoc": "A101",
  "thu": "Thứ Hai",
  "tietBatDau": 1,
  "tietKetThuc": 3,
  "thoiGian": "07:00 - 09:30",
  "ghiChu": "Mang theo laptop"
}
```
- **Response (201 Created):**
```json
{
  "message": "Thành công",
  "data": {
    "_id": "66b437c9ce982033cd76a63",
    "monHoc": "Lập trình Web",
    "giangVien": "ThS. Nguyễn Văn A",
    "phongHoc": "A101",
    "thu": "Thứ Hai",
    "tietBatDau": 1,
    "tietKetThuc": 3,
    "thoiGian": "07:00 - 09:30",
    "ghiChu": "Mang theo laptop",
    "createdAt": "2026-09-23T10:00:00.000Z",
    "updatedAt": "2026-09-23T10:00:00.000Z"
  }
}
```
- **Lỗi (500 Internal Server Error):** Dữ liệu không hợp lệ hoặc thiếu trường bắt buộc.
```json
{
  "error": "Lịch học validation failed: monHoc: Tên môn học là bắt buộc"
}
```

---

## 3. Lấy thông tin chi tiết lịch học theo ID
- **Route:** `GET /api/lich-hoc/{id}`
- **Mô tả:** Tìm kiếm và trả về thông tin của 1 lịch học theo mã `id`.
- **Tham số (Path Parameter):** `id` (Mã MongoDB ObjectId của lịch học).
- **Payload (Request Body):** *Không có*
- **Response (200 OK):**
```json
{
  "_id": "66b437c9ce982033cd76a63",
  "monHoc": "Lập trình Web",
  "giangVien": "ThS. Nguyễn Văn A",
  "phongHoc": "A101",
  "thu": "Thứ Hai",
  "tietBatDau": 1,
  "tietKetThuc": 3,
  "thoiGian": "07:00 - 09:30",
  "ghiChu": "Mang theo laptop",
  "createdAt": "2026-09-23T10:00:00.000Z",
  "updatedAt": "2026-09-23T10:00:00.000Z"
}
```
- **Lỗi (404 Not Found):**
```json
{
  "message": "Không tìm thấy"
}
```

---

## 4. Cập nhật thông tin lịch học theo ID
- **Route:** `PUT /api/lich-hoc/{id}`
- **Mô tả:** Cập nhật thông tin lịch học theo mã `id` và trả về thông tin mới sau khi sửa.
- **Tham số (Path Parameter):** `id` (Mã ID của lịch học cần cập nhật).
- **Payload (Request Body):** Gửi các trường cần cập nhật:
```json
{
  "monHoc": "Lập trình Web Nâng Cao",
  "giangVien": "TS. Trần Văn B",
  "phongHoc": "Lab 02",
  "thu": "Thứ Tư",
  "tietBatDau": 4,
  "tietKetThuc": 6,
  "thoiGian": "09:45 - 12:00",
  "ghiChu": "Kiểm tra giữa kỳ"
}
```
- **Response (200 OK):**
```json
{
  "_id": "66b437c9ce982033cd76a63",
  "monHoc": "Lập trình Web Nâng Cao",
  "giangVien": "TS. Trần Văn B",
  "phongHoc": "Lab 02",
  "thu": "Thứ Tư",
  "tietBatDau": 4,
  "tietKetThuc": 6,
  "thoiGian": "09:45 - 12:00",
  "ghiChu": "Kiểm tra giữa kỳ",
  "createdAt": "2026-09-23T10:00:00.000Z",
  "updatedAt": "2026-09-23T10:15:00.000Z"
}
```
- **Lỗi (404 Not Found):**
```json
{
  "message": "Lịch học không tồn tại (có thể đã bị xoá)"
}
```

---

## 5. Xóa lịch học theo ID
- **Route:** `DELETE /api/lich-hoc/{id}`
- **Mô tả:** Xóa bản ghi lịch học tương ứng với `id` khỏi hệ thống.
- **Tham số (Path Parameter):** `id` (Mã ID của lịch học cần xóa).
- **Payload (Request Body):** *Không có*
- **Response (200 OK):**
```json
{
  "message": "Đã xóa"
}
```
- **Lỗi (404 Not Found):**
```json
{
  "message": "Lịch học không tồn tại (có thể đã bị xoá)"
}
```
