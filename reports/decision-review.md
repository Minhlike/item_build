# Hồi quy thứ tự mua Thane SP

## Độ phủ dữ liệu

Chỉ mục upstream trỏ đến 130 tướng, 520 ô kỹ năng, 112 món, 88 ngọc, 31 nút phù hiệu, 9 phép và 5 chế độ tại đúng SHA nguồn. Có thể đi thẳng tới dòng chứa giá, icon hoặc kỹ năng ở bản gốc. Kho giữ dữ kiện biên tập độc lập và dẫn nguồn. Các bộ chiêu theo từng cấp, đường ghép và quyền mua trong client vẫn thiếu ở nhiều hồ sơ. [Chỉ mục nguồn](../knowledge/sources/upstream-locations.json) · [Điều khoản snapshot](https://github.com/MLuc24/lien-quan-data/blob/a210fe47690de7cefd18f76b61694724e02fdb5e/LICENSE)

Bản biên dịch có 130 hồ sơ tướng, 114 món và 88 ngọc. 89 tướng có ít nhất một thuộc tính ngoài định danh và chiến thuật, 85 tướng có dữ kiện LIVE_VN. Có 109 món có giá dưới một mức bằng chứng, trong đó 35 giá LIVE_VN. Có 14 đường ghép được lưu, gồm 7 đường LIVE_VN. Chín màu dùng ảnh Garena, gồm đủ hai build dưới đây. Chưa xác minh màu từ client. [Độ phủ](../knowledge/VERSION.json) · [Học viện trang bị](https://lienquan.garena.vn/hoc-vien/trang-bi/) · [Học viện ngọc](https://lienquan.garena.vn/hoc-vien/bang-ngoc/)

Ngoài hai đội hồi quy, hồ sơ đã tách hồi của Sephera khỏi thời gian không thể chọn, lá chắn trước khi đáp và hồi sau khi đáp của Xeniel, dấu chuẩn trong vùng phép của Aleister, xuyên giáp khi Elsu giữ vị trí và giảm giáp ở viền kỹ năng của Murad. Mô tả Học viện chưa ghi hiệu lực vẫn là ứng viên. [Sephera](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/sephera/) · [Xeniel](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/xeniel/) · [Aleister](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/aleister/) · [Elsu](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/elsu/) · [Murad](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/murad/)

## So cùng ngân sách

Pack nạp trước tính giá nguyên món, giữ nhãn bằng chứng cho từng giá và loại thành phần khỏi sáu slot cuối. Ca thử đặt 2.600 vàng cho đồ trợ thủ và giày cấp II, không có tiền bán đồ. So lộ trình tại mốc hòa ngân sách, giữ các phương án còn đánh đổi hoặc thiếu dữ kiện. Dồn, giao tranh kéo dài, nhịp rút và bảo kê được xét riêng. [Bảng trong FAST_DRAFT](../packs/l1/thane-support.json) · [Giao thức](../prompts/reasoning_protocol.md)

| Vàng tích lũy | So tại cùng ngân sách |
| ---: | --- |
| 4.600 | Sau đồ trợ thủ và giày còn 2.000. Giáp hiệp sĩ và Đai kháng phép có giá ứng viên 730 + 1.000. Tạm có 210 giáp, 700 HP và 110 giáp phép theo Học viện. Chỉ mua theo đường ghép nếu shop xác nhận món đích tiêu thụ thành phần. |
| 4.660–4.700 | Ra hoàn thành ở 4.660 theo giá LIVE_VN. Tới 4.700 có thể so cả Khiên thất truyền theo giá ứng viên. Khiên có thêm 200 HP và 50 giáp theo Học viện. Ra có giảm hồi 40% trong 3 giây từ lần Hỏa diệm trúng. |
| 4.780–4.920 | Gaia ở 4.780 theo giá LIVE_VN. Phù chú ở 4.790 và Troy ở 4.920 theo giá ứng viên. Khiên Thánh Quang có 1.000 HP, 180 giáp và 10% CDR LIVE_VN. Giá chưa đủ bằng chứng nên chưa thể xếp món này vào một mốc vàng. |
| 6.840–6.880 | 6.840 vừa đủ Ra → Gaia. Khiên thất truyền → Gaia còn thiếu 40 ở cùng mốc theo giá ứng viên. Tại 6.880, cả hai lộ trình hoàn thành theo giả định đó. Giữ chênh 40 vàng và so hiệu ứng trong cùng giao tranh. |
| 6.890–7.020 | Sau Khiên thất truyền, Phù chú có mốc ứng viên 6.890 và Troy 7.020. Troy cần lá chắn phép sẵn khi vào lại. Gaia có nhịp hồi sau kích hoạt. Khiên Thánh Quang đáng xét nếu Thane chạm được tướng trong lúc chủ lực ở gần và còn khiên. |

Giáp và Khiên thất truyền xử lý phần vật lý. Nội tại giảm tốc đánh có thể làm chậm tích dấu từ đánh thường nếu Hayate đánh người mang khiên. Chưa biết ảnh hưởng lên số phi tiêu hoặc tốc đánh được lấy lúc tung chiêu. Phần chuẩn đã xác minh của Hayate có gốc và hệ số AD, không có số hạng HP mục tiêu. Triệu Vân có nhiều thành phần chuẩn với hệ số chưa rõ. Dấu của Arthur có ứng viên sát thương **phép** theo HP đích. Lauriel vẫn có mâu thuẫn về loại sát thương của lần nổ dấu. [Hayate ngày 30/10](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-30-10-2026/) · [Lauriel và Triệu Vân ngày 05/02](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-tan-nien-khoi-the-05-02-2026/) · [Arthur](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/arthur/)

Ở 6.000 HP tối đa, phép thử Gaia cho 0 HP khi chưa phát sinh, 240 HP khi đủ điều kiện và 144 HP nếu toàn bộ lượng hồi chịu giảm hồi 40%. Phù chú có hai mức ứng viên ở cùng HP. Mỗi nhịp là 60 HP khi đang chịu áp lực hoặc 240 HP sau khi đủ khoảng nghỉ. Lá chắn và hồi có thời điểm tác dụng khác nhau. Giữ phần chưa rõ về hấp thụ sát thương chuẩn và cộng khiên. [Gaia](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-quang-minh-hac-am-18-12-2025/) · [Học viện trang bị](https://lienquan.garena.vn/hoc-vien/trang-bi/)

## Hai build đối chiếu

**C · Alice, Hayate, Arthur, Triệu Vân và Lauriel.** Khiên thất truyền có ưu thế nếu Thane thường xuyên chịu đánh thường. Giày kiên cường và Gaia sớm giúp đối phó vùng phép. Nếu chủ lực đang bị dồn và Thane mở lá chắn đúng nhịp, Khiên Thánh Quang có thể đổi quyết định khi xác minh được giá. Ra ở slot 5 để xử lý hồi của Lauriel và Triệu Vân khi còn bám nhau. Giảm hồi không xử lý khiên Alice. [Alice](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/alice/) · [Khiên Thánh Quang](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-vet-nut-thoi-khong-29-09-2026/)

Đại địa Mở trói 🟢 → Giày kiên cường 🔵 → Khiên thất truyền 🔵 → Giáp Gaia 🟢 → Áo choàng thần Ra 🔴 → Phù chú trường sinh 🟢

Mid đầu trận, đảo sông khi chủ lực an toàn. Rời vùng Alice, giữ đẩy để ngắt Hayate hoặc tách Triệu Vân. Kéo giao tranh ra khỏi pháp trận Lauriel.

**D · Evita, Toro, Hayate, Triệu Vân và Ryoma.** Build cũ lấy giảm hồi và lá chắn sớm. Khi đối chiếu cùng mốc, đường Ra → Khiên Thánh Quang thiếu nguồn kháng phép trước slot 5, trong lúc Ma vật chạm liên tục và giảm giáp phép. Giày hộ vệ có 10% giảm sát thương vật lý đã xác minh. Giày kiên cường đáng đổi khi Evita là nguồn áp lực chính và có khống chế mà giày thực sự rút ngắn. Dưới giả định Hỏa diệm ít phủ được nhịp hồi quan trọng, ưu tiên Phù chú ở slot 5. Giảm hồi tăng giá trị nếu Thane áp được đúng nhịp Ryoma đâm trúng hoặc Triệu Vân hút máu. [Evita ngày 15/10](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-15-10-2026/) · [Ryoma](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/ryoma/)

Đại địa Mở trói 🟢 → Giày hộ vệ ⚪ → Khiên thất truyền 🔵 → Giáp Gaia 🟢 → Phù chú trường sinh 🟢 → Áo choàng thần Ra 🔴

Mid đầu trận, đảo sông khi chủ lực an toàn. Né tâm vết nứt Evita. Giữ đẩy sau nhịp lao của Toro để cắt Hayate hoặc tách Triệu Vân.

## Truy xuất

| Đội | Pack trước form | Pack sau form tối đa | Token sau form |
| --- | ---: | ---: | ---: |
| C | 1 | 5 | 4.873 |
| D | 1 | 5 | 4.642 |

Pack chung khoảng 17,2 nghìn token, đếm bằng `o200k_base` trên tệp GitHub nguyên bản. C tại checkpoint trước có 15.792 token nạp trước và 4.431 token sau form. Hai đội dùng chung Hayate và Triệu Vân nên chuyển từ C sang D chỉ cần ba tệp, hoặc 0 khi mở lại đội đã nạp cùng SHA trong cùng ngữ cảnh. Các số 67 và 35 giây là thời gian Cloud người dùng cung cấp. Chưa có phép đo mới từ lúc gửi form tới build hoàn chỉnh trên ChatGPT Cloud. [Bootstrap](../prompts/cloud_bootstrap.md) · [Phép đo checkpoint trước](thane-fast-draft.md)
