# 🌐 HƯỚNG DẪN KHỞI CHẠY WEB APPLICATION (VINUNI AI LAB 3)
*Dành cho Role 4: Core Agent Developer / Integrator*

---

## 📌 1. TỔNG QUAN VỀ WEB APPLICATION

Ứng dụng Web này biến bài **Lab 03: Chatbot vs ReAct Agent** thành một giao diện **Web Studio hiện đại (Glassmorphism Dark Mode)** giúp cả nhóm và Giảng viên có thể tương tác trực quan:

1. 💬 **Live Chat Studio**: Chat trực tiếp với ReAct Agent và xem thời gian thực chuỗi suy luận `Thought 🧠` ➔ `Action 🛠️` ➔ `Observation 👁️` ➔ `Final Answer 🏁`.
2. ⚖️ **So Sánh Side-by-Side**: Cho phép gửi 1 câu hỏi để xem song song phản hồi từ **Chatbot Baseline (không dùng Tool)** và **ReAct Agent (gọi Tool thực tế)**.
3. 🧪 **Bộ 5 Test Cases Thử Thách**: Tải sẵn 5 câu test case của Đề tài 5 (Tra cứu & Đổi trả đơn hàng) để chạy nghiệm thu 1-click.
4. ⚙️ **Đổi LLM Provider Linh Hoạt**: Chuyển đổi nhanh giữa **Google Gemini**, **Offline Mock Mode**, **OpenAI** và **OpenRouter** trực tiếp trên Web.

---

## 🛠️ 2. HƯỚNG DẪN KHỞI CHẠY BẰNG CÁC BƯỚC

### 🔹 Bước 1: Mở Terminal tại thư mục dự án
Mở VS Code hoặc Terminal và đảm bảo đang ở thư mục gốc của bài Lab:
```bash
cd Day-3-Lab-Chatbot-vs-react-agent-E402
```

### 🔹 Bước 2: Kích hoạt môi trường ảo (Virtual Environment)
* **Trền Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **Trên macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 🔹 Bước 3: Cài đặt các thư viện phụ thuộc
Đảm bảo đã cài đủ thư viện (bao gồm `flask`):
```bash
python -m pip install -r requirements.txt
```

### 🔹 Bước 4: Kiểm tra cấu hình file `.env`
Kiểm tra file `.env` trong thư mục gốc:
* **Nếu muốn chạy AI Thật**: Chọn `LLM_PROVIDER=gemini` và dán `GEMINI_API_KEY=AIzaSy...`.
* **Nếu muốn chạy Offline Chạy Nhanh**: Chọn `LLM_PROVIDER=mock`.

### 🔹 Bước 5: Khởi chạy Web Server
Gõ lệnh sau để bật Web App:
```bash
python src/web_app.py
```

Màn hình Terminal sẽ hiển thị thông báo:
```text
==================================================
🏫 VINUNI AI LAB 3 WEB APP IS RUNNING AT:
👉 http://localhost:5000
==================================================
```

### 🔹 Bước 6: Truy cập trên Trình duyệt Web
Mở trình duyệt Web (Chrome, Edge, Firefox) và truy cập đường dẫn:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🎯 3. HƯỚNG DẪN SỬ DỤNG GIAO DIỆN WEB STUDIO

### 💬 1. Tab "Live Chat Studio"
* Nhập câu hỏi mẫu: `"Kiểm tra giúp tôi trạng thái đơn hàng ORD-1001"`
* Nhấn **Gửi** hoặc phím **Enter**.
* Quan sát Agent hiển thị từng thẻ suy luận `Step 1 — Thought`, `Action: get_order_status['ORD-1001']`, `Observation: ...` và câu trả lời cuối cùng `Final Answer`.

### ⚖️ 2. Tab "So Sánh Side-by-Side"
* Nhập câu hỏi: `"Tôi muốn đổi đơn ORD-1001 vì áo mặc không vừa size. Hãy kiểm tra và gửi yêu cầu đổi trả giúp tôi."`
* Bấm **So Sánh Ngay**.
* Cột trái sẽ cho thấy **Chatbot Baseline bị từ chối/không gọi được tool**, trong khi cột phải cho thấy **ReAct Agent gọi tool `get_order_status` ➔ `request_return` và xử lý thành công**.

### 🧪 3. Tab "Bộ 5 Test Cases"
* Bấm vào bất kỳ thẻ Test Case nào (Test #1 đến Test #5).
* Hệ thống sẽ tự động nạp câu hỏi sang Live Chat Studio để chạy nghiệm thu.

### ⚙️ 4. Tab "Cấu Hình Provider"
* Cho phép chọn nhà cung cấp AI mong muốn và bấm **Lưu Cấu Hình Provider**.

---

## 🚀 4. ĐỒNG BỘ NỘI DUNG LÊN GITHUB
Sau khi kiểm tra Web App chạy ổn định, đẩy code mới lên cho nhóm:
```bash
git add .
git commit -m "Role 4: Hoan thanh Web App UI va Huong dan chay Web"
git push origin main
```
