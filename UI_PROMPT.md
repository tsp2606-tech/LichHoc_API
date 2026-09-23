# Prompt Tạo Giao Diện Cho Dự Án CRUD LichHoc API

*Sử dụng nội dung dưới đây làm prompt (câu lệnh) cho các AI tạo code UI (như v0.dev, Claude 3.5 Sonnet, ChatGPT) để tự động sinh ra mã nguồn Frontend hoàn chỉnh cho ứng dụng Quản Lý Thời Khóa Biểu / Lịch Học.*

---

## 📌 Nội Dung Prompt (Copy phần bên dưới)

**Nhiệm vụ của bạn:**
Hãy đóng vai một chuyên gia phát triển Frontend và UI/UX Designer hàng đầu. Dựa trên các API mô tả dưới đây, hãy tạo một ứng dụng web Quản lý Lịch Học / Thời Khóa Biểu (Single Page Application) sử dụng React.js kết hợp với TailwindCSS và Lucide Icons (hoặc Shadcn UI).

**Yêu cầu về Thiết kế (UI/UX - Cực kỳ quan trọng):**
- Sử dụng phong cách thiết kế **hiện đại, cao cấp (Premium)**.
- Hiệu ứng **Glassmorphism** (kính mờ `backdrop-blur`), viền mỏng tinh tế, đổ bóng mềm mại (soft shadows) và các mảng màu gradient nhẹ nhàng.
- Tông màu (Color Palette): Hiện đại (Indigo, Violet, Emerald, Slate), có hỗ trợ chuyển đổi giao diện **Dark Mode / Light Mode** mượt mà.
- Typography: Font chữ hiện đại, rõ ràng (Inter, Roboto hoặc Plus Jakarta Sans).
- Animations: Micro-interactions mượt mà (hover effects, scale buttons, transitions khi mở modal/dialog, skeleton loader khi tải dữ liệu).
- Đảm bảo **Responsive 100%** trên Desktop, Tablet và Mobile.

**Các tính năng và luồng tương tác cần có:**
1. **Trang chủ & Xem Thời Khóa Biểu:**
   - Hỗ trợ 2 chế độ hiển thị linh hoạt (Toggle View):
     + **Dạng Thẻ Tuần (Weekly Timetable Grid):** Phân chia theo các cột Thứ trong tuần (Thứ Hai đến Chủ Nhật), mỗi cột chứa các card lịch học tương ứng.
     + **Dạng Danh Sách (Data Table / Card List):** Hiển thị danh sách đầy đủ với bộ lọc và tìm kiếm nhanh theo Tên môn học hoặc Giảng viên.
   - Thẻ lịch học hiển thị trực quan: Tên môn học (nổi bật), Giảng viên, Phòng học, Tiết học & Thời gian, Ghi chú, Badge trạng thái.
   - Gọi API: `GET /api/lich-hoc`

2. **Thêm lịch học mới:**
   - Nút bấm nổi bật "+ Thêm Lịch Học" (Add Schedule).
   - Mở Modal Form thêm lịch học gồm các trường:
     + Môn học (`monHoc`, text, bắt buộc)
     + Giảng viên (`giangVien`, text)
     + Phòng học (`phongHoc`, text)
     + Thứ (`thu`, select dropdown: Thứ Hai, Thứ Ba, Thứ Tư, Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ Nhật, bắt buộc)
     + Tiết bắt đầu & Tiết kết thúc (`tietBatDau`, `tietKetThuc`, number)
     + Khung giờ (`thoiGian`, text, ví dụ: 07:00 - 09:30)
     + Ghi chú (`ghiChu`, textarea)
   - Xử lý validation client và trạng thái loading khi submit form.
   - Gọi API: `POST /api/lich-hoc`

3. **Chỉnh sửa lịch học:**
   - Trong mỗi thẻ lịch học có nút "Sửa" (Edit).
   - Mở Modal Form và đổ sẵn toàn bộ dữ liệu hiện tại để người dùng chỉnh sửa.
   - Gọi API: `GET /api/lich-hoc/{id}` và `PUT /api/lich-hoc/{id}` khi lưu.

4. **Xóa lịch học:**
   - Nút "Xóa" (Delete) có màu đỏ cảnh báo.
   - Khi bấm, hiển thị Alert Dialog xác nhận: "Bạn có chắc chắn muốn xóa môn học này khỏi lịch học?".
   - Gọi API: `DELETE /api/lich-hoc/{id}`

5. **Thông báo phản hồi (Toast Notifications):**
   - Hiển thị pop-up Toast đẹp mắt ở góc màn hình khi Thêm, Sửa, Xóa thành công hoặc khi xảy ra lỗi kết nối.

**Thông tin các API để tích hợp (Base URL: `http://localhost:5000`):**
- **Lấy danh sách:** `GET /api/lich-hoc` (Trả về mảng các object `{ _id, monHoc, giangVien, phongHoc, thu, tietBatDau, tietKetThuc, thoiGian, ghiChu, createdAt, updatedAt }`)
- **Tạo mới:** `POST /api/lich-hoc` (Body: `{ monHoc, giangVien, phongHoc, thu, tietBatDau, tietKetThuc, thoiGian, ghiChu }`)
- **Lấy chi tiết:** `GET /api/lich-hoc/{id}`
- **Cập nhật:** `PUT /api/lich-hoc/{id}` (Body: `{ monHoc, giangVien, phongHoc, thu, tietBatDau, tietKetThuc, thoiGian, ghiChu }`)
- **Xóa:** `DELETE /api/lich-hoc/{id}`

Hãy viết mã nguồn Frontend hoàn chỉnh, chia nhỏ các components sạch sẽ và trực quan (Header, ScheduleCard, TimetableView, ScheduleModal, DeleteDialog).
