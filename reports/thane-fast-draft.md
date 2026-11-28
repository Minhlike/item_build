# FAST_DRAFT Thane SP

Hồi quy cho đấu hạng đơn VN tại mốc 27/11/2026. Địch đã nhập gồm Alice, Hayate, Arthur, Triệu Vân và Lauriel. Checkpoint trước tối ưu là `6e3a1f8ec62cad17cf14265e4abcf5f410fa2a54`.

## Tệp và số lượt đọc

Cloud nạp một pack dùng chung trước khi hiện form. Pack gồm mốc phiên bản, alias, bộ chiêu và sở thích Thane, chiến trường, chiến thuật và 43 món gồm các lựa chọn đang xem xét và thành phần. Sau khi nhận đội hình chỉ cần đọc song song tối đa năm pack tướng chưa có. Đổi một tên chỉ bổ sung một pack nếu bốn tướng còn lại vẫn trong ngữ cảnh. Mở L2/L3 theo ID khi cần một trường mới có thể đổi quyết định. [Pack](../packs/l1/thane-support.json) · [Bootstrap](../prompts/cloud_bootstrap.md)

| Đường đọc của ca hồi quy | Trước form | Sau form | Tổng |
| --- | ---: | ---: | ---: |
| Trước tối ưu, file được yêu cầu trong lượt cũ | 4 | 36 | 40 |
| Trước tối ưu, token nguyên file tương ứng | 3.769 | 32.773 | 36.542 |
| Sau tối ưu, file được yêu cầu | 2 | 5 | 7 |
| Sau tối ưu, token nguyên file tương ứng | 17.553 | 4.431 | 21.984 |

Đếm file trước form gồm bootstrap. Pack nạp trước chiếm 15.792 token ở ca đo. Token dùng tokenizer `o200k_base` trên file nguyên bản. Số liệu trước tối ưu tính lại từ các đường dẫn thực sự truy xuất ở ca 67 giây, kể cả lượt đọc lại VERSION. Token nền tảng thực sự cấp cho mô hình có thể khác. Lệnh `uv run item-build benchmark --progressive` xuất ca `cloud-67s`. 67 giây là số người dùng báo. Mục tiêu 5–10 giây cần đo lại cùng môi trường ChatGPT Cloud, từ gửi form đến build hoàn chỉnh.

Ba lượt kiểm tra được thực hiện qua connector GitHub trong Codex ở SHA `47bd3482ff865995e6ef9677e3f3fd3e4839201c`. Nạp pack chung mất 723, 589 và 720 ms. Đọc song song năm pack tướng và phân tích JSON mất 677, 773 và 709 ms. Cả ba lượt đọc được đầy đủ tướng, mẫu Alice–Hayate và sáu chấm màu. Các số này chỉ đo truy xuất, có thể chịu ảnh hưởng cache của connector và chưa bao gồm thời gian mô hình suy luận hay sinh câu trả lời.

## Cơ chế ảnh hưởng đến build

- **Hayate.** Phi tiêu có phần vật lý. Đủ sáu lần trúng cùng mục tiêu mới mở cửa sổ gây thêm chuẩn. Công thức chuẩn có phần gốc cộng theo AD, không có số hạng HP của nạn nhân. Học viện ghi có thể chí mạng, chưa chốt hệ số hoặc mọi loại nhịp. Tách nhiều lần nhận phi tiêu, tích đủ dấu và pha lao Bão phi tiêu. [Bản 30/10](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-30-10-2026/) · [Hướng dẫn chí mạng](https://hocvien.lienquan.garena.vn/bai-viet/34162)
- **Lauriel.** Hồ sơ tướng mô tả sát thương chuẩn diện rộng ở dấu thứ tư. Bản 05/02 kể cả “chuẩn” và “phép” trong cùng dòng hệ số theo cấp và AP. Giữ công thức đó ở trạng thái mâu thuẫn. Hồi phục đã xác minh có hệ số theo HP cộng thêm của Lauriel, tách khỏi sát thương lên đích. Thoát pháp trận giúp giới hạn số luồng và lần nổ dấu. [Hồ sơ](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/lauriel/) · [Bản 05/02](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-tan-nien-khoi-the-05-02-2026/) · [Bản 29/09](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-vet-nut-thoi-khong-29-09-2026/)
- **Alice.** Lá chắn đồng đội và hồi chiêu S2 có bản vá. Choáng, câm lặng, làm chậm và giảm giáp phép trong vùng có mô tả chính thức chưa ghi ngày. Chưa có tỷ lệ giảm giáp phép hoặc phép thử Mở trói trong từng nhịp khi bước vào lại vùng. Lá chắn Alice cho Hayate thêm thời gian bắn nếu cả hai cùng có góc. [Bản 13/08](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-ngay-hoi-lien-quan-13-08-2026/) · [Hồ sơ](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/alice/)
- **Triệu Vân.** S2 có công thức vật lý, hút máu và hồi chiêu theo cấp từ bản vá. Long kích và đòn sau Long kích có mô tả sát thương chuẩn chưa ghi ngày. Hệ số chuẩn và cơ sở HP của hai phần vẫn thiếu. Chừa công cụ tách khỏi chủ lực sau khi đối thủ đã áp sát. [Bản 05/02](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-tan-nien-khoi-the-05-02-2026/) · [Hồ sơ](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/trieu-van/)
- **Arthur.** Lá chắn S2 tính theo HP tối đa của Arthur. Hồ sơ mô tả dấu S1 gây thêm sát thương **phép** theo HP tối đa nạn nhân, riêng phần đánh cường hóa là vật lý. Chiêu cuối có nguồn ghi theo HP người tung, nguồn khác ghi theo HP đích. Giữ hai cách đọc riêng khi ước lượng giá trị mua HP. [Bản 13/08](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-ngay-hoi-lien-quan-13-08-2026/) · [Hồ sơ](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/arthur/) · [Hướng dẫn Học viện](https://hocvien.lienquan.garena.vn/bai-viet/37791)

## So mốc mua 3–4

Mốc 2.600 vàng là tổng giá nguyên món Đại địa Mở trói và Giày kiên cường. Bảng giả định chưa có thành phần của món tiếp theo, không có tiền bán đồ và không giả định giá nâng cấp. Giá ứng viên chỉ dùng để kiểm tra độ nhạy. Viết `Q` cho giá nguyên món Khiên Thánh Quang chưa biết. [Danh mục Garena](https://lienquan.garena.vn/hoc-vien/trang-bi/)

| Món | Tổng ở slot 3 | Tổng ở slot 4 sau Gaia | Tình huống tăng giá trị |
| --- | ---: | ---: | --- |
| Khiên Thánh Quang | 2.600 + Q | 4.780 + Q | Giáp, HP và lá chắn đã có bản vá. Muốn che chủ lực cần gây sát thương lên tướng trong lúc đồng minh ở gần và hiệu ứng sẵn sàng. Khả năng chắn chuẩn chưa đủ bằng chứng. |
| Khiên thất truyền | 4.700 ứng viên | 6.880 ứng viên | Ứng viên HP, giáp và giảm tốc đánh khi chịu đòn. Có lợi hơn nếu Hayate duy trì nhiều đòn đánh thường. Chưa suy số nhịp phi tiêu bị giảm. |
| Giáp Gaia | 4.780 theo giá nguyên món | Đã sở hữu | Giá và lượng hồi 4% HP tối đa mỗi lần phát sinh đã xác minh. Kháng phép và thời gian kích hoạt còn là ứng viên. Có ích khi chống cả cấu rỉa phép và đợt áp sát. |
| Huân chương Troy | 4.920 ứng viên | 7.100 ứng viên | Ứng viên kháng phép và lá chắn phép sau khi rời giao tranh. Hợp khi đợt phép mở đầu đe dọa nhất và lá chắn sẵn. |
| Phù chú trường sinh | 4.790 ứng viên | 6.970 ứng viên | Ứng viên HP, song giáp và hồi qua nhiều nhịp. Nhịp hồi cao yêu cầu có khoảng nghỉ không nhận đòn từ tướng hoặc trụ. |

Nếu đã mua Khiên Thánh Quang ở slot 3, các mốc slot 4 là `4.700 + Q` cho Khiên thất truyền, `4.780 + Q` cho Gaia, `4.790 + Q` cho Phù chú và `4.920 + Q` cho Troy. Ba tổng chứa giá ứng viên vẫn là tình huống giả định. Thử `purchase-plan` với báo giá Gaia bằng giá nguyên món, không tiêu thụ thành phần, xác nhận 4.780 vừa đủ và 4.779 thiếu một vàng. Chạy không báo giá vẫn trả thiếu công thức khi đang có đồ. Lộ trình dừng ở Khiên Thánh Quang vì thiếu giá. [Luật lá chắn](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-vet-nut-thoi-khong-29-09-2026/) · [Giá và hồi Gaia](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-quang-minh-hac-am-18-12-2025/)

Ví dụ độ nhạy ở 6.000 HP tối đa, giữ HP bằng nhau để so hiệu ứng. Gaia hồi 240 HP khi nội tại phát sinh, hoặc 144 nếu chịu giảm hồi 40% trong toàn cửa sổ. Phù chú là ứng viên, tương ứng 60 HP mỗi nhịp khi đang chịu áp lực hoặc 240 khi đủ điều kiện nhịp hồi cao. Chưa cộng dồn các nguồn. Các lượng hồi này không bảo đảm đủ để sống qua sát thương đến trước nhịp hồi.

**Build hồi quy có điều kiện** · Đại địa Mở trói 🟢 → Giày kiên cường 🔵 → Khiên Thánh Quang 🟡 → Giáp Gaia 🟢 → Áo choàng thần Ra 🔴 → Phù chú trường sinh 🟢.

Mid đầu trận, đảo sông khi chủ lực an toàn. Tránh đứng trong vùng Alice và nhận phi tiêu liên tiếp. Giữ đẩy để ngắt Hayate hoặc tách Triệu Vân, rút khỏi vùng Lauriel khi giao tranh kéo dài.

Màu cả sáu món lấy từ ảnh Garena theo tên. Kho phân biệt cách nhận diện ảnh với màu hiển thị của cửa hàng trong client. Build vẫn có điều kiện về ngân sách Khiên Thánh Quang, hiệu lực Mở trói và chỉ số ứng viên. [Ảnh Khiên Thánh Quang](https://lienquan.garena.vn/wp-content/uploads/2026/09/unnamed-4.png) · [Ảnh danh mục](https://lienquan.garena.vn/hoc-vien/trang-bi/)
