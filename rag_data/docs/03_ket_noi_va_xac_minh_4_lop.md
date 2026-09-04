# Kết nối & Xác minh 4 Lớp (Handshake)

## Làm thế nào để tìm kiếm người dùng khác?
Nhập **chính xác địa chỉ Gmail** của người bạn muốn kết nối vào ô tìm kiếm trên thanh bên trái (sidebar). Ứng dụng **chỉ hỗ trợ tìm kiếm chính xác theo Gmail** — bạn phải nhập đầy đủ địa chỉ email, ví dụ: `bob@gmail.com`. Hệ thống không gợi ý danh sách người dùng công khai để bảo vệ quyền riêng tư.

## Tôi tìm kiếm theo tên được không?
**Không.** Ứng dụng chỉ cho phép tìm kiếm bằng **địa chỉ Gmail chính xác**. Bạn không thể tìm theo tên hiển thị hay gợi ý bằng một phần tên. Điều này nhằm bảo vệ quyền riêng tư — chỉ người biết chính xác Gmail của bạn mới có thể kết nối với bạn.

## Làm thế nào để bắt đầu một cuộc trò chuyện với người khác?
Để bắt đầu cuộc trò chuyện, bạn cần trải qua **quy trình xác minh 4 lớp bắt buộc**:
1. **Tìm kiếm**: Nhập chính xác Gmail của người đó vào ô tìm kiếm và nhấn **"Bắt đầu chat bảo mật"**.
2. **Lớp 2 – Chờ chấp nhận**: Người kia sẽ nhận được lời mời kết nối. Họ cần đăng nhập và nhấn **"Chấp nhận lời mời"**.
3. **Lớp 3 – Trao đổi khóa**: Hệ thống tự động thực hiện trao đổi khóa mã hóa giữa hai bên.
4. **Lớp 4 – Xác nhận mã an toàn**: Cả hai bên nhìn thấy cùng một **mã 6 chữ số** (ví dụ: `842 910`). Nhấn **"Xác nhận khớp mã"** để hoàn tất.

Sau khi hoàn thành 4 lớp, kênh chat được mở khóa và bạn có thể bắt đầu nhắn tin.

## Người tôi muốn chat đang offline thì sao?
**Không sao cả.** Quy trình kết nối 4 lớp hoạt động **không đồng bộ (asynchronous)** — bạn có thể gửi lời mời kể cả khi người kia đang offline. Lời mời sẽ được lưu trên máy chủ. Khi người đó đăng nhập lại, họ sẽ thấy thông báo **"[Tên bạn] muốn kết nối"** và có thể chấp nhận hoặc từ chối.

## Mã an toàn 6 chữ số là gì?
**Mã an toàn (Safety Code)** là một chuỗi 6 chữ số (ví dụ: `842 910`) được tính toán tự động từ khóa công khai của cả hai bên. Đây là xác minh **Lớp 4** trong quy trình bảo mật. Mục đích là đảm bảo không có ai đứng giữa đánh cắp kết nối của bạn (tấn công Man-in-the-Middle). Nếu hai bên thấy cùng một mã, hãy nhấn **"Xác nhận khớp mã"** để hoàn tất thiết lập kênh bảo mật.

## Tại sao tôi không thể gửi tin nhắn dù đã kết nối?
Bạn **chỉ có thể gửi tin nhắn sau khi hoàn thành đủ 4 lớp xác minh**. Hệ thống sẽ khóa ô nhập tin nhắn cho đến khi:
- Lớp 1: Cả hai đều có tài khoản Google hợp lệ
- Lớp 2: Người nhận đã chấp nhận lời mời
- Lớp 3: Trao đổi khóa mã hóa hoàn tất
- Lớp 4: Cả hai đã xác nhận mã an toàn

Nếu bất kỳ lớp nào chưa hoàn thành, hãy kiểm tra trạng thái cuộc trò chuyện và hoàn tất bước còn lại.

## Người kia từ chối lời mời kết nối của tôi thì sao?
Nếu người kia **từ chối lời mời** ở Lớp 2, lời mời kết nối sẽ bị hủy và không có kênh chat nào được tạo. Bạn sẽ không thể gửi tin nhắn cho họ. Bạn có thể thử gửi lại lời mời sau.

## Re-handshake là gì và khi nào cần thực hiện?
**Re-handshake** là quy trình xác minh lại 4 lớp bảo mật cho một cuộc trò chuyện **đã tồn tại**. Bạn cần thực hiện khi:
- Bạn hoặc người kia **đăng nhập trên thiết bị/trình duyệt mới**.
- Bạn hoặc người kia **xóa dữ liệu trình duyệt**.
- Hệ thống hiển thị banner cảnh báo **"Khóa bảo mật đã thay đổi"**.

Trong khi re-handshake đang diễn ra, ô nhập tin nhắn bị khóa để đảm bảo không có tin nhắn nào bị gửi với khóa sai.

## Làm thế nào để thực hiện re-handshake?
1. Mở cuộc trò chuyện — hệ thống sẽ tự động phát hiện sự thay đổi khóa và hiển thị **banner cảnh báo màu vàng/đỏ**.
2. Nhấn nút **"Xác minh lại"** (Re-verify) trên banner.
3. Hoàn thành lại **4 lớp xác minh** (tương tự như lần kết nối đầu tiên).
4. Sau khi cả hai bên xác nhận **mã an toàn mới 6 chữ số**, cuộc trò chuyện trở về trạng thái **VERIFIED_ACTIVE**.

Toàn bộ quá trình mất dưới **30 giây** nếu cả hai bên đang online.

## Sau khi re-handshake, tin nhắn cũ có đọc được không?
Trên thiết bị/trình duyệt mới **không có cache cục bộ**, bạn sẽ **không đọc được tin nhắn cũ** vì chúng được mã hóa bằng khóa cũ đã mất. Hệ thống sẽ hiển thị một **đường phân cách bảo mật** (security timeline divider) trong luồng chat, thông báo rằng một phiên E2EE mới đã được thiết lập. Từ đó trở đi, các tin nhắn mới sẽ được mã hóa và giải mã bình thường.
