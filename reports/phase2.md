# Bàn giao Phase 2

**PARTIAL_READY dành cho tra cứu và so sánh có điều kiện.** Phiên bản VN tham chiếu là Vết Nứt Thời Không 26/11/2026. Hồ sơ công khai hỗ trợ tư vấn có dẫn nguồn khi dữ liệu đủ cho tướng, vai trò và tình huống. Còn thiếu dữ liệu để bảo đảm một build hoàn chỉnh cho mọi tướng. [Thông báo bản VN](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-26-11-2026/)

## Độ bao phủ

| Chỉ số | Checkpoint Phase 1 | Phase 2 |
| --- | ---: | ---: |
| Mục tướng | 130 | 130 |
| Tướng có thuộc tính LIVE_VN | 18 | 46 |
| Thành phần cơ chế tướng LIVE_VN | 34 | 79 |
| Pack trang bị | 8 | 57 |
| Trang bị có thuộc tính LIVE_VN | 3 | 23 |
| Công thức ghép có bản ghi hiệu lực | 0 | 7 |
| Pack ngọc | 5 | 18, đều là ứng viên |
| Thuộc tính chiến trường LIVE_VN | 11 | 31 |

- Ingest rà soát **130 tướng, 520 bản ghi kỹ năng/nội tại, 796 đoạn mô tả và 1.742 dòng chỉ số** từ snapshot đã pin. Chỉ mục rà soát cục bộ có thêm số liệu của 112 trang bị, 88 ngọc, 4 nhánh phù hiệu, 9 phép và 5 chế độ. Vị trí từ khóa giữ nguyên đoạn nguồn, kể cả phủ định và ngoại lệ. Phần này chịu giới hạn phân phối của upstream. [Checksum và phiên bản nguồn](upstream-audit.json)
- Đã thêm công thức ghép có linh kiện và số lượng từ các bản tháng 1 và tháng 4. Có giá, chỉ số, thao tác tay/tự động, khoảng kích hoạt và điều kiện theo từng thuộc tính khi nguồn cung cấp. Ví dụ Rhea cần hai Huyết trượng, Tróc nã dùng cùng tên nội tại, Phản Pháo của Giáp thống khổ cần bấm. Luật chồng Tróc nã chi tiết còn chờ thử. [Trang bị tháng 1](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-tan-nien-khoi-the-21-01-2026/) · [Trang bị tháng 4](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-le-hoi-5v5-08-04-2026/)
- Phù chú trường sinh có hai nhịp hồi ứng viên với điều kiện chịu đòn riêng. Khiên Thánh Quang có điều kiện gây sát thương lên tướng và cửa sổ lá chắn. Giữ bất định phần công phép Quả cầu băng sương và loại sát thương cơ bản Excalibur khi nguồn ghi khác nhau. [Danh mục trang bị](https://lienquan.garena.vn/hoc-vien/trang-bi/) · [Bản 29/09](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-vet-nut-thoi-khong-29-09-2026/) · [Bản 13/08](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-ngay-hoi-lien-quan-13-08-2026/)
- Chiến trường có thêm Bọ Ánh Sáng, bùa cường hóa và chia sẻ, phòng xâm lăng, vàng lính giữa, kinh tế trợ thủ, máu trụ và tăng sức mạnh lính cuối trận. Mốc Ma chủng hắc ám tháng 11 thay thế hệ số tháng 9. [Bản 08/07](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-ngay-hoi-lien-quan-08-07-2026/) · [Bản 17/11](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-17-11-2026/)

## Truy xuất và kiểm định

Một lượt đánh giá Thane hỗ trợ đọc 3 pack nhóm thay vì 27 tệp cùng dữ liệu, giảm từ 11.234 xuống 10.063 token. Ca chuẩn bị pháp sư giảm từ 48 xuống 6 tệp và từ 16.707 xuống 14.537 token. Kiểm tra đọc ngược đối chiếu điều kiện, trạng thái, nguồn và trường chưa xác minh. Số tệp là mô hình cho số lượt gọi khi mỗi lượt đọc một tệp. [Kết quả benchmark](catalog-benchmark.json)

Hồ sơ Thane SP loại Giáp thống khổ và món phải bấm ngoài nhóm trợ thủ, yêu cầu xem mốc 3–4 và đánh giá Phù chú trường sinh theo trận. Hai ca hồi quy kiểm tra phạm vi áp dụng, bằng chứng sát thương, điều kiện Ma nhãn và sự khác nhau giữa hồi máu định kỳ với lá chắn. Kinh nghiệm từng trận vẫn ở hồ sơ đánh giá cá nhân. [Hai ca hồi quy](../evaluations/phase2_cases.json) · [Hồ sơ Thane SP](../sources/preferences/thane-support.json)

32 kiểm thử tự động, gồm cả hồi quy Phase 1, tính toàn vẹn nhóm, trạng thái ứng viên và công thức. Bộ nghiệm thu suy luận có 11 câu độc lập và rubric. Phần yêu cầu P5 được cung cấp dừng giữa câu đầu. Bộ câu hỏi bám mục tiêu nghiệm thu đọc được. Chưa có kết quả chạy tác nhân Cloud độc lập hoặc độ trễ đo trên connector. [Bộ nghiệm thu](../evaluations/reasoning.md)

## Xác minh tiếp theo

- Đối chiếu toàn bộ bộ kỹ năng, chỉ số gốc/tăng trưởng và các hồi chiêu còn thiếu với client hoặc nguồn có ngày. Các bản ghi kiểm toán cục bộ và mô tả ứng viên có thể chỉ điểm chỗ cần xác minh.
- Kiểm kê cửa hàng đầy đủ theo phiên bản, gồm giá, công thức, icon, phạm vi Ma nhãn, trần CDR và ràng buộc mua đồ trợ thủ. Xác nhận các luật chọn ngọc, phù hiệu và phép trong client.
- Kiểm tra lịch lính, quái, mục tiêu và kinh tế còn thiếu. Rà mốc hết hiệu lực theo mùa.
- Chạy bộ nghiệm thu từ một phiên ChatGPT Cloud mới ở đúng SHA. Tự động theo dõi HTML Garena cần quyền nguồn theo registry. [Registry](../knowledge/sources/registry.json)
