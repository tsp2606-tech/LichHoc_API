import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import swaggerUi from 'swagger-ui-express';
import swaggerJsdoc from 'swagger-jsdoc';
import connectDB from './config/db.js';
import lichHocRoutes from './routes/lichHocRoutes.js';

dotenv.config();
const app = express();

// Middleware CORS
const allowedOrigins = [
  'http://localhost:3000',
  'http://localhost:5174',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5174',
];

app.use(
  cors({
    origin: function (origin, callback) {
      // Cho phép request không có Origin (Postman, Swagger, curl, server-to-server)
      if (!origin) {
        return callback(null, true);
      }
      if (allowedOrigins.includes(origin)) {
        return callback(null, true);
      }
      return callback(new Error('Not allowed by CORS'));
    },
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
  })
);

app.use(express.json());

// Kết nối Cơ sở dữ liệu
connectDB();

// Cấu hình Swagger OpenAPI 3.0
const swaggerOptions = {
  definition: {
    openapi: '3.0.3',
    info: {
      title: 'Quản Lý Lịch Học API (LichHoc API)',
      version: '1.0.0',
      description: 'Tài liệu OpenAPI 3.0 / Swagger UI cho dịch vụ Quản lý Lịch học sinh viên (CRUD LichHoc API)',
    },
    servers: [
      {
        url: '/',
        description: 'Local Development Server',
      },
    ],
  },
  apis: ['./src/routes/*.js'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Mount routes
app.use('/api/lich-hoc', lichHocRoutes);
app.use('/api/lichhoc', lichHocRoutes); // Alias hỗ trợ gọi không có dấu gạch nối

const PORT = process.env.PORT || 5001;
const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on: http://localhost:${PORT}`);
  console.log(`📚 Swagger Docs available at: http://localhost:${PORT}/api-docs`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Cổng ${PORT} đã bị chiếm dụng bởi tiến trình khác. Vui lòng tắt tiến trình cũ hoặc đổi PORT trong .env.`);
  } else {
    console.error('❌ Lỗi khởi động máy chủ:', err.message);
  }
});
