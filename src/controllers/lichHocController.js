import * as lichHocService from '../services/lichHocService.js';

export const create = async (req, res) => {
  try {
    const lichHoc = await lichHocService.createLichHoc(req.body);
    res.status(201).json({ message: 'Thành công', data: lichHoc });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAll = async (req, res) => {
  try {
    const listLichHoc = await lichHocService.getAllLichHoc();
    res.status(200).json(listLichHoc);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getDetail = async (req, res) => {
  try {
    const lichHoc = await lichHocService.getLichHocById(req.params.id);
    if (!lichHoc) {
      return res.status(404).json({ message: 'Không tìm thấy' });
    }
    res.status(200).json(lichHoc);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const update = async (req, res) => {
  try {
    const lichHoc = await lichHocService.updateLichHoc(req.params.id, req.body);
    if (!lichHoc) {
      return res.status(404).json({ message: 'Lịch học không tồn tại (có thể đã bị xoá)' });
    }
    res.status(200).json(lichHoc);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const remove = async (req, res) => {
  try {
    const lichHoc = await lichHocService.deleteLichHoc(req.params.id);
    if (!lichHoc) {
      return res.status(404).json({ message: 'Lịch học không tồn tại (có thể đã bị xoá)' });
    }
    res.status(200).json({ message: 'Đã xóa' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
