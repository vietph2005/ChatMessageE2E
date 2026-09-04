# Bảo mật & Mã hóa Đầu cuối (E2EE)

## Tin nhắn của tôi có bị ai đọc được không?
**Không.** Ứng dụng sử dụng mã hóa đầu cuối (End-to-End Encryption — E2EE) với thuật toán **AES-256-GCM**. Tin nhắn được mã hóa ngay trên thiết bị của bạn trước khi gửi đi. Máy chủ **chỉ lưu trữ dữ liệu đã mã hóa** — không ai, kể cả nhà phát triển ứng dụng, có thể đọc nội dung tin nhắn của bạn. Chỉ bạn và người nhận (với khóa giải mã cục bộ) mới đọc được.

## Khóa riêng tư của tôi có được lưu trên server không?
**Tuyệt đối không.** Khóa riêng tư (Private Key) được tạo ra và lưu trữ **hoàn toàn trên trình duyệt của bạn** (trong IndexedDB) và không bao giờ được gửi lên máy chủ. Đây là nguyên tắc **Zero-Knowledge** — máy chủ không có khả năng giải mã bất kỳ tin nhắn nào của bạn.

## Làm thế nào để xem chi tiết bảo mật của một cuộc trò chuyện?
1. Mở cuộc trò chuyện bạn muốn kiểm tra.
2. Nhấn vào nút **"Chi tiết bảo mật"** (Security Details) trên header của cuộc trò chuyện.
3. Bảng thông tin sẽ hiển thị:
   - Trạng thái của **4 lớp xác minh**
   - **Mã an toàn 60 chữ số** đầy đủ (SHA-256 fingerprint)
   - **Mã QR** để xác minh trực tiếp
   - Lịch sử xác minh

## Tôi nhận được thông báo "Mã an toàn đã thay đổi" là sao?
Thông báo này xuất hiện khi **khóa mã hóa của người kia đã thay đổi** — thường do họ đăng nhập trên thiết bị mới hoặc xóa dữ liệu trình duyệt. Đây là cảnh báo bảo mật quan trọng. Bạn cần thực hiện **xác minh lại (re-handshake)** để đảm bảo vẫn đang chat với đúng người. Nhấn **"Xác minh lại"** và hoàn thành lại 4 lớp xác minh.
