import express from 'express';
import { create, getAll, getDetail, update, remove } from '../controllers/lichHocController.js';

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     LichHoc:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           description: "Mã ID duy nhất của lịch học (MongoDB ObjectId)"
 *           example: "66b437c9ce982033cd76a63"
 *         monHoc:
 *           type: string
 *           description: "Tên môn học"
 *           example: "Lập trình Web"
 *         giangVien:
 *           type: string
 *           description: "Tên giảng viên giảng dạy"
 *           example: "ThS. Nguyễn Văn A"
 *         phongHoc:
 *           type: string
 *           description: "Phòng học hoặc link học online"
 *           example: "A101"
 *         thu:
 *           type: string
 *           description: "Thứ trong tuần"
 *           example: "Thứ Hai"
 *         tietBatDau:
 *           type: integer
 *           description: "Tiết bắt đầu"
 *           example: 1
 *         tietKetThuc:
 *           type: integer
 *           description: "Tiết kết thúc"
 *           example: 3
 *         thoiGian:
 *           type: string
 *           description: "Khung giờ học cụ thể"
 *           example: "07:00 - 09:30"
 *         ghiChu:
 *           type: string
 *           description: "Ghi chú thêm"
 *           example: "Mang theo laptop"
 *         createdAt:
 *           type: string
 *           format: date-time
 *           description: "Thời điểm tạo"
 *         updatedAt:
 *           type: string
 *           format: date-time
 *           description: "Thời điểm cập nhật gần nhất"
 *     CreateLichHocInput:
 *       type: object
 *       required:
 *         - monHoc
 *         - thu
 *       properties:
 *         monHoc:
 *           type: string
 *           description: "Tên môn học (Bắt buộc)"
 *           example: "Lập trình Web"
 *         giangVien:
 *           type: string
 *           description: "Tên giảng viên"
 *           example: "ThS. Nguyễn Văn A"
 *         phongHoc:
 *           type: string
 *           description: "Phòng học"
 *           example: "A101"
 *         thu:
 *           type: string
 *           description: "Thứ trong tuần (Bắt buộc)"
 *           example: "Thứ Hai"
 *         tietBatDau:
 *           type: integer
 *           description: "Tiết bắt đầu (Mặc định 1)"
 *           example: 1
 *         tietKetThuc:
 *           type: integer
 *           description: "Tiết kết thúc (Mặc định 3)"
 *           example: 3
 *         thoiGian:
 *           type: string
 *           description: "Khung giờ học"
 *           example: "07:00 - 09:30"
 *         ghiChu:
 *           type: string
 *           description: "Ghi chú"
 *           example: "Mang theo laptop"
 *     UpdateLichHocInput:
 *       type: object
 *       properties:
 *         monHoc:
 *           type: string
 *           example: "Lập trình Web Nâng Cao"
 *         giangVien:
 *           type: string
 *           example: "TS. Trần Văn B"
 *         phongHoc:
 *           type: string
 *           example: "Lab 02"
 *         thu:
 *           type: string
 *           example: "Thứ Tư"
 *         tietBatDau:
 *           type: integer
 *           example: 4
 *         tietKetThuc:
 *           type: integer
 *           example: 6
 *         thoiGian:
 *           type: string
 *           example: "09:45 - 12:00"
 *         ghiChu:
 *           type: string
 *           example: "Kiểm tra giữa kỳ"
 *     CreateLichHocSuccessResponse:
 *       type: object
 *       properties:
 *         message:
 *           type: string
 *           example: "Thành công"
 *         data:
 *           $ref: '#/components/schemas/LichHoc'
 *     DeleteSuccessResponse:
 *       type: object
 *       properties:
 *         message:
 *           type: string
 *           example: "Đã xóa"
 *     ErrorResponse:
 *       type: object
 *       properties:
 *         message:
 *           type: string
 *           example: "Không tìm thấy"
 *         error:
 *           type: string
 *           example: "Lỗi chi tiết từ hệ thống"
 */

/**
 * @swagger
 * /api/lich-hoc:
 *   post:
 *     summary: Thêm lịch học mới
 *     description: Tạo một bản ghi lịch học mới trong cơ sở dữ liệu. Yêu cầu `monHoc` và `thu`.
 *     tags: [Lịch Học]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/CreateLichHocInput'
 *           example:
 *             monHoc: "Lập trình Web"
 *             giangVien: "ThS. Nguyễn Văn A"
 *             phongHoc: "A101"
 *             thu: "Thứ Hai"
 *             tietBatDau: 1
 *             tietKetThuc: 3
 *             thoiGian: "07:00 - 09:30"
 *             ghiChu: "Mang theo laptop"
 *     responses:
 *       201:
 *         description: Tạo lịch học mới thành công
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/CreateLichHocSuccessResponse'
 *             example:
 *               message: "Thành công"
 *               data:
 *                 _id: "66b437c9ce982033cd76a63"
 *                 monHoc: "Lập trình Web"
 *                 giangVien: "ThS. Nguyễn Văn A"
 *                 phongHoc: "A101"
 *                 thu: "Thứ Hai"
 *                 tietBatDau: 1
 *                 tietKetThuc: 3
 *                 thoiGian: "07:00 - 09:30"
 *                 ghiChu: "Mang theo laptop"
 *                 createdAt: "2026-09-23T10:00:00.000Z"
 *                 updatedAt: "2026-09-23T10:00:00.000Z"
 *       500:
 *         description: Lỗi máy chủ hoặc dữ liệu không hợp lệ
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *             example:
 *               error: "Lịch học validation failed: monHoc: Tên môn học là bắt buộc"
 */
router.post('/', create);

/**
 * @swagger
 * /api/lich-hoc:
 *   get:
 *     summary: Lấy danh sách tất cả lịch học
 *     description: Trả về danh sách mảng gồm tất cả lịch học trong cơ sở dữ liệu.
 *     tags: [Lịch Học]
 *     responses:
 *       200:
 *         description: Trả về mảng danh sách lịch học thành công
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/LichHoc'
 *             example:
 *               - _id: "66b437c9ce982033cd76a63"
 *                 monHoc: "Lập trình Web"
 *                 giangVien: "ThS. Nguyễn Văn A"
 *                 phongHoc: "A101"
 *                 thu: "Thứ Hai"
 *                 tietBatDau: 1
 *                 tietKetThuc: 3
 *                 thoiGian: "07:00 - 09:30"
 *                 ghiChu: "Mang theo laptop"
 *                 createdAt: "2026-09-23T10:00:00.000Z"
 *                 updatedAt: "2026-09-23T10:00:00.000Z"
 */
router.get('/', getAll);

/**
 * @swagger
 * /api/lich-hoc/{id}:
 *   get:
 *     summary: Lấy thông tin chi tiết lịch học theo ID
 *     description: Tìm kiếm và trả về thông tin chi tiết của 1 lịch học theo mã id.
 *     tags: [Lịch Học]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Mã ID (MongoDB ObjectId) của lịch học
 *         example: "66b437c9ce982033cd76a63"
 *     responses:
 *       200:
 *         description: Lấy chi tiết lịch học thành công
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/LichHoc'
 *             example:
 *               _id: "66b437c9ce982033cd76a63"
 *               monHoc: "Lập trình Web"
 *               giangVien: "ThS. Nguyễn Văn A"
 *               phongHoc: "A101"
 *               thu: "Thứ Hai"
 *               tietBatDau: 1
 *               tietKetThuc: 3
 *               thoiGian: "07:00 - 09:30"
 *               ghiChu: "Mang theo laptop"
 *               createdAt: "2026-09-23T10:00:00.000Z"
 *               updatedAt: "2026-09-23T10:00:00.000Z"
 *       404:
 *         description: Không tìm thấy lịch học
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *             example:
 *               message: "Không tìm thấy"
 */
router.get('/:id', getDetail);

/**
 * @swagger
 * /api/lich-hoc/{id}:
 *   put:
 *     summary: Cập nhật thông tin lịch học theo ID
 *     description: Cập nhật thông tin lịch học theo mã id và trả về thông tin mới sau khi sửa.
 *     tags: [Lịch Học]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Mã ID của lịch học cần cập nhật
 *         example: "66b437c9ce982033cd76a63"
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UpdateLichHocInput'
 *           example:
 *             monHoc: "Lập trình Web Nâng Cao"
 *             giangVien: "TS. Trần Văn B"
 *             phongHoc: "Lab 02"
 *             thu: "Thứ Tư"
 *             tietBatDau: 4
 *             tietKetThuc: 6
 *             thoiGian: "09:45 - 12:00"
 *             ghiChu: "Kiểm tra giữa kỳ"
 *     responses:
 *       200:
 *         description: Cập nhật lịch học thành công
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/LichHoc'
 *             example:
 *               _id: "66b437c9ce982033cd76a63"
 *               monHoc: "Lập trình Web Nâng Cao"
 *               giangVien: "TS. Trần Văn B"
 *               phongHoc: "Lab 02"
 *               thu: "Thứ Tư"
 *               tietBatDau: 4
 *               tietKetThuc: 6
 *               thoiGian: "09:45 - 12:00"
 *               ghiChu: "Kiểm tra giữa kỳ"
 *               createdAt: "2026-09-23T10:00:00.000Z"
 *               updatedAt: "2026-09-23T10:15:00.000Z"
 *       404:
 *         description: Lịch học không tồn tại
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *             example:
 *               message: "Lịch học không tồn tại (có thể đã bị xoá)"
 */
router.put('/:id', update);

/**
 * @swagger
 * /api/lich-hoc/{id}:
 *   delete:
 *     summary: Xóa lịch học theo ID
 *     description: Xóa lịch học tương ứng với id khỏi hệ thống.
 *     tags: [Lịch Học]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Mã ID của lịch học cần xóa
 *         example: "66b437c9ce982033cd76a63"
 *     responses:
 *       200:
 *         description: Xóa lịch học thành công
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/DeleteSuccessResponse'
 *             example:
 *               message: "Đã xóa"
 *       404:
 *         description: Lịch học không tồn tại
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 *             example:
 *               message: "Lịch học không tồn tại (có thể đã bị xoá)"
 */
router.delete('/:id', remove);

export default router;
