# Nhắn tin & Đa phương tiện

## Làm thế nào để gửi tin nhắn?
Sau khi kênh chat được xác minh (trạng thái **VERIFIED_ACTIVE**), bạn có thể:
1. Nhập nội dung tin nhắn vào ô nhập liệu ở cuối màn hình chat.
2. Nhấn **Enter** hoặc nút **Gửi** để gửi tin nhắn.

Tin nhắn sẽ được mã hóa ngay trên thiết bị của bạn trước khi truyền đi. Người nhận sẽ nhận được trong vòng dưới 500ms nếu họ đang online.

## Ứng dụng hỗ trợ những loại tin nhắn nào?
Ứng dụng hiện hỗ trợ:
- Tin nhắn văn bản (text)
- Biểu tượng cảm xúc (emoji)
- Hình ảnh mã hóa (JPG, PNG, GIF — dung lượng tối đa **5MB**)

Tất cả nội dung đều được mã hóa đầu cuối (E2EE) trước khi gửi. Chưa hỗ trợ voice/video call hay file đính kèm khác trong phiên bản hiện tại.

## Tôi gửi tin nhắn khi người kia offline thì có nhận được không?
**Có.** Nếu người nhận đang offline, tin nhắn đã mã hóa sẽ được **lưu trữ trên máy chủ** và tự động gửi đến ngay khi họ kết nối lại. Trạng thái tin nhắn sẽ cập nhật từ **Đã gửi → Đã nhận → Đã đọc** theo thời gian thực.

## Các trạng thái tin nhắn có nghĩa gì?
Mỗi tin nhắn sẽ hiển thị một trong các trạng thái sau:
- **Đang gửi** – Tin nhắn đang được mã hóa và truyền đi.
- **Đã gửi** ✓ – Máy chủ đã nhận được tin nhắn.
- **Đã nhận** ✓✓ – Thiết bị của người nhận đã tải về tin nhắn.
- **Đã đọc** ✓✓ (xanh) – Người nhận đã mở và đọc tin nhắn.

## Làm thế nào để gửi hình ảnh?
1. Trong khung chat đang mở, nhấn vào **biểu tượng hình ảnh** (hoặc ghim kẹp) trên thanh nhập liệu.
2. Chọn file ảnh từ thiết bị của bạn (định dạng JPG, PNG, hoặc GIF, dung lượng tối đa **5MB**).
3. Nhấn **Gửi**.

Hình ảnh sẽ được mã hóa ngay trên thiết bị của bạn trước khi truyền. Người nhận sẽ thấy ảnh hiển thị trong bong bóng chat sau khi giải mã cục bộ.

## Ứng dụng hỗ trợ gửi video không?
**Chưa hỗ trợ.** Phiên bản hiện tại chỉ hỗ trợ gửi hình ảnh (JPG, PNG, GIF tối đa 5MB). Tính năng gửi video và file lớn sẽ được xem xét trong các phiên bản tương lai.

## Làm thế nào để thu hồi tin nhắn?
Để **thu hồi tin nhắn cho cả hai phía** (Unsend for Everyone):
1. Di chuột vào bong bóng tin nhắn bạn muốn thu hồi.
2. Nhấn vào biểu tượng **ba chấm** (⋯) xuất hiện.
3. Chọn **"Thu hồi cho mọi người"** (Unsend for Everyone).

Kết quả: Tin nhắn sẽ bị thay thế bằng dòng chữ *"Tin nhắn này đã được thu hồi"* trên **cả hai** màn hình.

## Xóa tin nhắn ở phía tôi là gì?
**Xóa ở phía tôi** (Delete for Me) chỉ xóa tin nhắn khỏi **màn hình của bạn**. Người nhận **vẫn thấy tin nhắn đó** như bình thường. Chức năng này không ảnh hưởng đến dữ liệu trên máy chủ hay màn hình của người kia.

## Sự khác nhau giữa Thu hồi cho mọi người và Xóa ở phía tôi?
| Chức năng | Ảnh hưởng phía bạn | Ảnh hưởng phía người kia |
|---|---|---|
| **Thu hồi cho mọi người** | Tin nhắn biến mất | Tin nhắn bị thay bằng "Đã thu hồi" |
| **Xóa ở phía tôi** | Tin nhắn biến mất | Người kia vẫn thấy bình thường |

## Làm thế nào để biết người kia đang gõ tin nhắn?
Khi người kia đang gõ, bạn sẽ thấy **chỉ báo gõ phím** (typing indicator) hiển thị trong cửa sổ chat — thường là dạng ba chấm nhảy (···). Chỉ báo này cập nhật theo thời gian thực và biến mất khi họ dừng gõ hoặc gửi tin nhắn.

## Làm thế nào để biết người kia đang online hay offline?
Trong danh sách cuộc trò chuyện và header của khung chat, bạn sẽ thấy:
- Chấm xanh bên cạnh ảnh đại diện: Người đó đang **online**.
- Không có chấm hoặc trạng thái mờ: Người đó đang **offline**.

Trạng thái online được cập nhật theo thời gian thực qua kết nối WebSocket.
