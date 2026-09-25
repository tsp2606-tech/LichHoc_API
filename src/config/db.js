import mongoose from 'mongoose';

const connectDB = async () => {
  try {
    const mongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017/lich_hoc';
    await mongoose.connect(mongoUri);
    console.log('✅ MongoDB Connected');
  } catch (error) {
    console.error('❌ Connection Failed:', error.message);
    console.warn('⚠️ Server vẫn tiếp tục chạy. Vui lòng kiểm tra kết nối mạng hoặc IP Whitelist trên MongoDB Atlas.');
  }
};

export default connectDB;
