# Chặn Liên hệ & Xử lý Sự cố

## Làm thế nào để chặn một người dùng?
1. Mở cuộc trò chuyện với người bạn muốn chặn.
2. Nhấn vào nút **"Chi tiết bảo mật"** hoặc biểu tượng thông tin (ℹ️) trên header.
3. Chọn **"Chặn liên hệ"** (Block Contact) và xác nhận.

Sau khi chặn, người đó **không thể gửi tin nhắn hay khởi tạo cuộc trò chuyện mới** với bạn. Cuộc trò chuyện sẽ chuyển sang trạng thái **BLOCKED**.

## Làm thế nào để bỏ chặn một người?
1. Tìm cuộc trò chuyện với người bạn đã chặn (sẽ hiển thị nhãn **"Đã bị chặn"**).
2. Nhấn vào nút **"Bỏ chặn liên hệ"** (Unblock Contact).
3. Xác nhận hành động.

Nếu khóa mã hóa của cả hai bên **không thay đổi** kể từ khi chặn, cuộc trò chuyện sẽ ngay lập tức khôi phục về **VERIFIED_ACTIVE** và bạn có thể nhắn tin lại. Nếu khóa đã thay đổi, hệ thống sẽ yêu cầu **xác minh lại 4 lớp**.

## Tôi bỏ chặn nhưng người kia vẫn chặn tôi thì sao?
Chặn là **quan hệ một chiều**. Nếu bạn bỏ chặn người kia nhưng **họ vẫn còn đang chặn bạn**, bạn vẫn không thể nhắn tin cho họ. Cuộc trò chuyện sẽ vẫn bị hạn chế cho đến khi người kia cũng bỏ chặn bạn.

## Giao diện ứng dụng trông như thế nào?
Giao diện được thiết kế theo phong cách **Facebook Messenger**, bao gồm:
- **Thanh bên trái (Sidebar)**: Danh sách cuộc trò chuyện, sắp xếp theo tin nhắn gần nhất, badge số tin nhắn chưa đọc, và ô tìm kiếm Gmail.
- **Khu vực chat giữa**: Bong bóng tin nhắn (tin nhắn của bạn bên phải, tin nhắn người kia bên trái), dấu thời gian, trạng thái đọc.
- **Bảng thông tin bên phải**: Chi tiết bảo mật, mã an toàn, lịch sử xác minh.

Giao diện hỗ trợ **chế độ tối (dark mode)** và **responsive** từ điện thoại (360px) đến màn hình 4K (2560px).

## Ứng dụng có hoạt động trên điện thoại không?
**Có.** Giao diện hỗ trợ đầy đủ trên điện thoại. Khi dùng màn hình nhỏ:
- Sidebar cuộc trò chuyện **ẩn đi** và chỉ hiện khu vực chat.
- Có nút **quay lại** (back) để trở về danh sách cuộc trò chuyện.
- Giao diện tự động điều chỉnh cho màn hình từ **360px trở lên**.

## Tôi thấy thông báo "Tin nhắn không thể giải mã" thì phải làm gì?
Thông báo **"Tin nhắn không thể giải mã"** xảy ra khi dữ liệu tin nhắn bị hỏng hoặc khóa phiên không khớp. Các bước xử lý:
1. Thử tải lại trang (F5 hoặc Ctrl+R).
2. Nếu vẫn còn lỗi, kiểm tra xem bạn có đang dùng **đúng trình duyệt** đã khởi tạo khóa ban đầu không.
3. Nếu bạn vừa đăng nhập trên thiết bị mới, hãy thực hiện **re-handshake** với người đó.
4. Nếu lỗi vẫn tiếp tục, liên hệ hỗ trợ.

## Mất kết nối mạng giữa chừng thì tin nhắn có bị mất không?
**Không bị mất.** Hệ thống có cơ chế tự động:
- **Kết nối WebSocket** sẽ tự động kết nối lại với **exponential backoff** khi mạng phục hồi.
- Tin nhắn đã gửi sẽ được **lưu trữ tạm** và gửi lại.
- Tin nhắn từ người kia trong lúc bạn offline sẽ **được giao ngay** khi bạn kết nối lại.

Quá trình handshake bị gián đoạn giữa chừng cũng sẽ **tiếp tục tự động** mà không mất trạng thái.
