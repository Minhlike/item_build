# Chỉnh sửa có bằng chứng

Thêm tệp JSON theo `schemas/patch.schema.json`, dùng ID riêng và trỏ `evidence` tới bằng chứng đăng ký. Cùng một thuộc tính không thể có hai giá trị hiệu lực cùng ngày. Khi sửa thông tin của đúng ngày hiệu lực cũ, sửa dữ kiện gốc cùng bằng chứng và dùng commit để lưu lịch sử chỉnh sửa. Dữ liệu thu thập cục bộ không được hợp nhất tự động vào thư mục này.
