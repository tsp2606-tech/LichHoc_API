import mongoose from 'mongoose';

const lichHocSchema = new mongoose.Schema(
  {
    monHoc: {
      type: String,
      required: [true, 'Tên môn học là bắt buộc'],
      trim: true,
    },
    giangVien: {
      type: String,
      default: '',
      trim: true,
    },
    phongHoc: {
      type: String,
      default: '',
      trim: true,
    },
    thu: {
      type: String,
      required: [true, 'Thứ trong tuần là bắt buộc'],
      trim: true,
    },
    tietBatDau: {
      type: Number,
      default: 1,
      min: 1,
    },
    tietKetThuc: {
      type: Number,
      default: 3,
      min: 1,
    },
    thoiGian: {
      type: String,
      default: '',
      trim: true,
    },
    ghiChu: {
      type: String,
      default: '',
      trim: true,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('LichHoc', lichHocSchema);
