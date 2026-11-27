# Bàn giao 27/11/2026

**PARTIAL_READY.** Kho hỗ trợ tra cứu bằng chứng theo tướng và đọc thay đổi cân bằng trên máy chủ VN. Phiên bản tham chiếu là Vết Nứt Thời Không, cập nhật 26/11/2026. Danh sách công khai của Garena và danh sách upstream khớp 130 mục sau khi ánh xạ ID `11596` thành `edras`. Hai dạng Flowborn được giữ thành hai ID. Danh sách khóa/chọn trực tiếp trong client còn cần xác minh. [Thông báo VN 26/11](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-26-11-2026/) · [Danh sách Garena](https://lienquan.garena.vn/hoc-vien/tuong-skin/)

| Nhóm | Snapshot kiểm định cục bộ | Pack công khai | Có thuộc tính LIVE_VN |
| --- | ---: | ---: | ---: |
| Tướng | 130 | 130 | 18 |
| Kỹ năng và nội tại | 520, trong đó 130 nội tại | 81 thuộc tính cơ chế tướng ở hồ sơ gốc | 34 thuộc tính cơ chế |
| Trang bị | 112 | 8 | 3 |
| Ngọc | 88 | 5 | 0 |
| Phù hiệu | 4 nhánh, 31 nút | 4 nhánh | 2 nhánh, 2 nút |
| Phép bổ trợ | 9 | 11 | 3 |
| Chế độ và chiến trường | 5 chế độ | 1 pack xếp hạng | 1 pack, 11 thuộc tính |

Các thuộc tính cơ chế được đếm theo thành phần riêng, vì một chiêu có thể có nhiều thành phần hoặc cấu hình. Những mục chỉ có định danh và nguồn công khai có pack riêng để truy xuất và theo dõi chỗ thiếu.

## Kiểm định dữ liệu

- 103 tướng upstream có ít nhất một chỉ số gốc. Thane thiếu toàn bộ chỉ số gốc. 17 tướng có ít nhất một mục lịch sử cân bằng. 520 kỹ năng có mô tả, không có trường hồi chiêu được chuẩn hóa trong snapshot.
- 23 tướng có cụm sát thương chuẩn trong mô tả nhưng nhãn tổng chỉ ghi vật lý hoặc phép. Bolt Baron có thành phần sát thương phép từ đòn đánh và từ chiêu riêng. Chiêu 3 của Thane có mô tả khác nhau về thành phần gốc giữa trang kỹ năng và thông báo tháng 8. Các tái dựng hệ số cần kiểm thử đúng phiên bản. [Bolt Baron](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/bolt-baron/) · [Thane](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/thane/) · [Bản 13/08](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-ngay-hoi-lien-quan-13-08-2026/)
- 112 trang bị upstream có ít nhất một dòng chỉ số và 87 có nội tại. Công thức ghép chưa có trường riêng, Khiên Thánh Quang vắng trong upstream. Hồ sơ công khai bổ sung Khiên Thánh Quang từ thông báo Garena, bao gồm khác biệt giữa người đánh gần và đánh xa. 86/88 viên ngọc upstream có dòng chỉ số. [Bản 29/09](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-vet-nut-thoi-khong-29-09-2026/)
- Chu kỳ hồi lượt Trừng trị, thời gian giãn cách dùng lượt và giảm thời gian hồi còn lại theo kỹ năng được biểu diễn riêng. Với công thức theo cấp thiếu mốc, hệ thống giữ hệ số nguồn và yêu cầu bằng chứng bổ sung trước khi tính. [Bản 08/07](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-ngay-hoi-lien-quan-08-07-2026/)

Chi tiết theo thuộc tính và checksum nằm trong [upstream-audit.json](upstream-audit.json). Snapshot pin tại `a210fe47690de7cefd18f76b61694724e02fdb5e`. Các tệp bị giới hạn phân phối nằm cục bộ theo registry.

## Kiểm thử và benchmark

25 kiểm thử bao gồm bốn đội hình hồi quy, sáu nhóm vai trò, xác thực cơ sở và đơn vị, dữ liệu khác máy chủ, điều kiện theo patch, kiểm tra canonical/pack và mô phỏng ETag, robots và nội dung bị sửa. CLI update chạy idempotent trên snapshot hiện tại.

Benchmark Windows trên bốn ca đầy đủ, mỗi ca 200 lượt truy xuất sau khi nạp. p95 nóng từ **0,039–0,044 ms**. Lượt đọc đầu sau khi nạp index từ **2,19–2,38 ms**, 15 tệp mỗi ca kể cả index và bằng chứng. JSON compact giữ nguyên dữ liệu benchmark, từ **23.985–26.918 byte** và **6.474–7.289 token** với `o200k_base`. JSON thụt lề là 9.099–10.288 token. Markdown bọc JSON là 6.538–7.353 token. Ba định dạng qua kiểm tra đọc ngược. Kết quả đo giải mã nằm trong [benchmark.json](benchmark.json). Chất lượng suy luận và độ trễ kết nối ChatGPT Cloud còn cần đo riêng.

## Phần việc tiếp nối

1. Đối chiếu bộ chiêu, dạng và các cơ chế hồi phục, sát thương, khống chế của tướng còn thiếu bằng thông báo Garena và kiểm thử trong game. Ưu tiên các rủi ro từ bốn ca hồi quy, gồm ngưỡng nội tại Thane, nhịp Allain, thời lượng Ma nhãn và tương tác với Kaine.
2. Kiểm kê cửa hàng hiện hành và điền giá, thành phần, màu icon, giới hạn giảm hồi chiêu, luật trang bị trợ thủ và các ngoại lệ. Kiểm tra số lượng ngọc và nhánh phù hiệu hợp lệ trước khi dùng MODE A để chốt cấu hình.
3. Bổ sung lịch lính, quái và bùa, tiền/EXP và cửa sổ mục tiêu theo từng patch. Điền hiệu lực hoặc đánh dấu thiếu với mỗi cơ chế theo mùa.
4. Đăng ký quyền nguồn trước khi mở giám sát HTTP Garena. Rà thông báo công khai theo hướng dẫn [cập nhật](../README.md#cập-nhật-và-khôi-phục), sau đó ghi thay đổi cấp thuộc tính, biên dịch và kiểm định. Chạy lại các prompt tại một commit cố định khi có môi trường ChatGPT Cloud để nghiệm thu.
