# Bàn giao Phase 3 · 27/11/2026

Kho vẫn ở mức **PARTIAL_READY** cho rank đơn VN, bản vá 26/11/2026. Phase 3 mở rộng bằng chứng và thêm công cụ so sánh tại mốc mua và theo thời gian. Mốc so sánh Phase 2 là `b0146c96f82f2652ddb1184b27763b3ad5a7c2da`. Bản đã dùng để kiểm thử gói đối chứng C là `61cc7af37fd3131e78fea14a616daf8c6a9f562e`. [Thông báo bản vá](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-26-11-2026/)

## Độ bao phủ

| Chỉ tiêu | Phase 2 | Phase 3 |
| --- | ---: | ---: |
| Mục tướng, gồm hai ID Flowborn | 130 | 130 |
| Hồ sơ tướng đủ bằng chứng theo thuộc tính bắt buộc | 0 | 0 |
| Tướng có ít nhất một thuộc tính LIVE_VN | 46 | 83 |
| Thuộc tính tướng LIVE_VN | 84 | 241 |
| Cơ chế tướng LIVE_VN | 79 | 233 |
| Ô kỹ năng có ít nhất một cơ chế / có số liệu | 66 / 47 | 148 / 112 |
| Ô có hồi chiêu / đủ dữ kiện tính hồi chiêu | 15 / 2 | 38 / 3 |
| Ô có thời lượng / ngoại lệ / tương tác | 4 / 4 / 0 | 12 / 9 / 6 |
| Ô chỉ số gốc hoặc tăng trưởng LIVE_VN | 0 / 2.080 | 2 / 2.080 |
| Trang bị trong kho / có giá LIVE_VN / có công thức ghép LIVE_VN | 57 / 14 / 7 | 57 / 14 / 7 |
| Trang bị có ít nhất một thuộc tính LIVE_VN / icon có màu xác minh | 23 / 0 | 23 / 0 |
| Hồ sơ ngọc trong kho / có thuộc tính LIVE_VN | 18 / 0 | 27 / 0 |
| Nhánh phù hiệu có thuộc tính LIVE_VN | 2 / 4 | 2 / 4 |
| Hồ sơ phụ trợ và dạng nâng cấp có thuộc tính LIVE_VN | 3 / 11 | 4 / 12 |
| Thuộc tính chiến trường LIVE_VN | 31 | 37 |
| Cơ chế LIVE_VN cộng ở tướng, đồ, ngọc, phù hiệu, phép và chiến trường | 124 | 291 |
| Tệp biên dịch | 474 | 495 |

Một hồ sơ đủ cần kiểm chứng toàn bộ danh mục chiêu và dạng, các chỉ số gốc/tăng trưởng bắt buộc, và duyệt từng ô về lượng, hồi chiêu, thời lượng, điều kiện, ngoại lệ và tương tác. Thuộc tính không áp dụng cần có ghi nhận đã duyệt. Số ô đo được là 535 và 536, trong đó Phase 3 kiểm thêm Chiêu 4 của Dirak. Mỗi cột đếm ô có ít nhất một thuộc tính tương ứng. Mốc cấp chưa rõ vẫn giữ hệ số công bố và không được tính vào hồi chiêu đủ dữ kiện. [Ma trận 130 hồ sơ](phase3-coverage.json)

Đối chiếu snapshot ghim `a210fe47690de7cefd18f76b61694724e02fdb5e` cho 130 mục, 520 dòng kỹ năng và ứng viên chỉ số gốc của 103 mục. Trường cooldown tường minh bằng 0. Snapshot còn có 112 trang bị, 88 ngọc, thiếu công thức ghép tường minh và thiếu Khiên Thánh Quang. Toàn văn và số liệu theo tướng từ nguồn này nằm trong bản rà soát cục bộ theo registry. Các số liệu Phase 3 dựa trên sự kiện và trị số biên tập riêng từ thông báo được phép trích dữ kiện, với lịch sử thay đổi. [Kiểm định upstream](upstream-audit.json) · [Quyền nguồn](../knowledge/sources/registry.json)

## Suy luận và kiểm định

- Có 8 mẫu tương tác đội địch có điều kiện và 8 chiến thuật rank đơn theo vùng, tài nguyên, giai đoạn và rủi ro. Ví dụ, Raz và Natalya chỉ tạo cửa sổ chung khi cùng tiếp xúc vào đúng lúc giảm giáp phép hiệu lực. Cặp Dextra–Sinestrea cần quan sát Hiến tế và thời hạn Ước nguyện. [Giao thức Cloud](../prompts/reasoning_protocol.md) · [Dữ liệu chiến thuật](../sources/tactics.json)
- Lộ trình mua theo vàng dừng đúng ở bước không đủ vàng hoặc chưa biết giá. Hai nhánh thử Thane SP chạm slot 3 và 4, với nhánh lên Khiên trước tiêu đúng một thành phần. Giá nâng cấp chưa đủ bằng chứng trong kho nên ví dụ nhập báo giá giả định. [Kịch bản mua](../examples/purchase-plan.json)
- Trong bài tính giả định, hướng giáp còn 4.075 HP so với 3.975 HP ở hướng thêm máu. Khi dùng cặp tỷ lệ nhận sát thương giả định sau xuyên, kết quả đổi thành 3.700 so với 3.900 HP. Phép tính theo mốc chính thức của Florentino cho 504 chuẩn mỗi lần với 700 công vật lý theo cơ sở nguồn và đích 8.000 HP tối đa. Các điều kiện hồi máu, trần CDR do kịch bản nhập, lá chắn và bất định đều có kiểm thử xác định. [Kịch bản độ nhạy](../examples/what-if.json) · [Cơ chế Florentino](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-quang-minh-hac-am-4-12-2025/)
- Nghiên cứu năm bài và hai kho mã đã được ghi cùng giới hạn, quyền sử dụng và phần nguyên lý triển khai. [Ghi chú nghiên cứu](phase3-research.md)
- Bộ kiểm định độc lập có 56 tình huống, năm vị trí, sáu lớp tướng và tám chiều chấm. Thử đóng gói tạo 168 lượt với cùng đề. Kết quả tổng hợp trống đúng với 0 lượt đã chạy/chấm. Phiên làm việc chưa có quyền gọi mô hình Cloud độc lập cho ba nhánh, nên chưa có số liệu chất lượng LLM. [Hướng dẫn chạy A/B/C](../evaluations/phase3/README.md)

## Chi phí truy xuất

Năm đội hình Thane SP được đo cùng đầu vào, Windows, tokenizer `o200k_base`, 200 vòng lặp mỗi tình huống. JSON ngữ cảnh gọn tăng từ 9.504–9.998 lên 11.427–14.083 token khi bật Phase 3. Số file tri thức lạnh tăng từ 15 lên 16, gồm một pack chiến thuật. Cách gửi từng file thô cộng prompt cần khoảng 33.161–34.464 token ở Phase 2 và 40.057–41.303 ở Phase 3, tương ứng 17 hoặc 19 file nếu đếm cả prompt. Ước tính file thô bao gồm toàn bộ chỉ mục bằng chứng. Tra bằng CLI hoặc lọc nguồn theo ID có thể tránh gửi phần chỉ mục không liên quan. Phép đo tập trung vào đầu vào, chưa có token sinh, giá tiền hoặc độ trễ connector thực tế.

Pack nhóm đồ hỗ trợ đọc 3 file thay vì 27, từ 11.234 còn 10.063 token cho cùng thuộc tính. Benchmark kiểm tra giải mã qua lại và sự đồng nhất của các pack nhóm. [Số đo và checksum](phase3-benchmark.json)

## Khoảng trống ảnh hưởng chốt build

- Chưa đủ dữ liệu có hiệu lực để hoàn thiện trọn bộ kỹ năng, chỉ số gốc, tăng trưởng và ngưỡng theo cấp. Danh sách công khai vẫn cần đối chiếu khả năng chọn trong hàng chờ. Nguồn dated mới chủ yếu là bản chênh lệch từng kỹ năng. Một số ghi chú mâu thuẫn hoặc không ghi loại sát thương/mốc cấp.
- Chưa có đủ đối chiếu cửa hàng cho toàn bộ giá, công thức ghép, màu icon, quyền mua và cộng dồn. Chưa khóa luật ngọc/phù hiệu, phạm vi phụ trợ theo hàng chờ, trần CDR tổng quát, công thức giáp/xuyên và lịch đầy đủ cho mọi tài nguyên. Biểu tượng dùng ⚪ ở chỗ thiếu bằng chứng. Sáu món chỉ được chốt khi vượt qua kiểm tra căn cứ.
- Cần nguồn được phép cho các trường còn thiếu và lượt chạy đối chứng trên cùng mô hình Cloud. Chưa có căn cứ để kết luận độ chính xác hoặc cải thiện chất lượng trả lời Cloud theo các chiều chấm.
