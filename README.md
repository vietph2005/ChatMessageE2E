# Full-Stack Starter Project

[![Java CI](https://img.shields.io/badge/Java-17%2B-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3.3-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Vite + React](https://img.shields.io/badge/React-18.3-blue.svg)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)

Dự án mẫu khởi tạo sạch (clean boilerplate) giữ nguyên toàn bộ Tech Stack chuẩn bao gồm Backend **Spring Boot 3** và Frontend **React + Vite + TypeScript + Tailwind CSS**, sẵn sàng để xây dựng các tính năng mới từ đầu.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

### Backend
- **Java 17 & Spring Boot 3.3.3**
- **Spring Web & Spring WebSocket** (STOMP messaging)
- **Spring Data MongoDB**
- **Spring Security & JJWT** (Stateless authentication)
- **Lombok**
- **JUnit 5 & Spring Boot Test**

### Frontend
- **React 18 & TypeScript 5**
- **Vite 5** (Fast Build & Hot Module Replacement)
- **Tailwind CSS 3 & PostCSS**
- **Lucide Icons**
- **STOMP / SockJS client**
- **Vitest & React Testing Library**

---

## 🚀 Khởi chạy dự án

### Yêu cầu môi trường
- **JDK 17+**
- **Maven 3.8+**
- **Node.js 18+ & npm**
- **MongoDB** (mặc định: `mongodb://localhost:27017/chat_message_e2e`)

### 1. Khởi chạy Backend
```bash
# Compile mã nguồn
mvn clean compile

# Chạy ứng dụng Spring Boot
mvn spring-boot:run
```
Backend sẽ lắng nghe tại `http://localhost:8080`.

### 2. Khởi chạy Frontend
```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies (nếu chưa có)
npm install

# Khởi chạy dev server
npm run dev
```
Frontend sẽ chạy tại `http://localhost:5173`.

### 3. Build Production
```bash
# Build frontend
cd frontend && npm run build

# Package backend JAR
mvn clean package -DskipTests
```
