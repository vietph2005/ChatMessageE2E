# Đăng nhập & Quản lý Tài khoản

## Làm thế nào để đăng nhập vào ứng dụng?
Bạn đăng nhập bằng tài khoản Google (Gmail). Trên màn hình đầu tiên, nhấn nút **"Đăng nhập bằng Google"** (Sign in with Google), sau đó hoàn tất luồng xác thực Google OAuth2. Sau khi đăng nhập thành công, hệ thống sẽ tự động tải thông tin hồ sơ của bạn (tên, email, ảnh đại diện) và khởi tạo khóa mã hóa cục bộ trên trình duyệt.

## Ứng dụng hỗ trợ đăng nhập bằng tài khoản gì?
Ứng dụng **chỉ hỗ trợ đăng nhập bằng tài khoản Google (Gmail)**. Bạn phải có một địa chỉ Gmail hợp lệ để sử dụng. Không hỗ trợ đăng nhập bằng email thông thường, Facebook, hay các tài khoản khác.

## Tôi đăng nhập trên máy tính mới thì tin nhắn cũ có mất không?
Có, **tin nhắn cũ sẽ không hiển thị** trên thiết bị/trình duyệt mới. Vì lý do bảo mật, khóa riêng tư (private key) và lịch sử tin nhắn được lưu **cục bộ trong trình duyệt** (IndexedDB) và không bao giờ được tải lên máy chủ. Khi đăng nhập trên trình duyệt mới, hệ thống sẽ tự tạo cặp khóa mới và thông báo cho các liên lạc của bạn rằng **mã an toàn (Safety Code) đã thay đổi**. Từ đó, bạn chỉ thấy được những tin nhắn mới sau khi thực hiện xác minh lại (re-handshake).

## Tôi xóa cache trình duyệt thì sao?
Nếu bạn xóa dữ liệu trình duyệt (cache, IndexedDB), **khóa mã hóa cục bộ sẽ bị mất**. Khi đăng nhập lại, hệ thống sẽ tự động tạo cặp khóa mới và yêu cầu bạn thực hiện lại quy trình xác minh 4 lớp (re-handshake) với từng liên lạc. Đây là thiết kế bảo mật để bảo vệ quyền riêng tư — private key không bao giờ rời khỏi thiết bị của bạn.

## Phiên đăng nhập hết hạn thì phải làm gì?
Khi phiên đăng nhập hết hạn, hệ thống sẽ tự động **chuyển hướng bạn về trang đăng nhập** và hiển thị thông báo yêu cầu đăng nhập lại. Chỉ cần nhấn **"Đăng nhập bằng Google"** và hoàn tất OAuth flow. Khóa mã hóa cục bộ vẫn được giữ nguyên (trừ khi bạn xóa dữ liệu trình duyệt).
