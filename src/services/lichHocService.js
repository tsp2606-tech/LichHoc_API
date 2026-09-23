import LichHoc from '../models/lichHocModel.js';

export const createLichHoc = (data) => LichHoc.create(data);
export const getAllLichHoc = () => LichHoc.find().sort({ createdAt: -1 });
export const getLichHocById = (id) => LichHoc.findById(id);
export const updateLichHoc = (id, data) => LichHoc.findByIdAndUpdate(id, data, { new: true, returnDocument: 'after', runValidators: true });
export const deleteLichHoc = (id) => LichHoc.findByIdAndDelete(id);
