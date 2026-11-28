# Nghiệm thu tác nhân đọc ITEM_BUILD

Chạy từng câu trong phiên mới tại cùng SHA, chỉ cấp quyền đọc kho. Ghi tệp đã mở và thời gian nếu đo được. Chấm 0 nếu sai hoặc biến ứng viên thành dữ kiện, 1 nếu đúng ý chính còn thiếu điều kiện, 2 nếu nêu đúng điều kiện và trạng thái bằng chứng. Chấm riêng từng câu. Hai ca đầu dùng [dữ liệu trận](phase2_cases.json).

| Câu hỏi độc lập | Tiêu chí đạt 2 điểm |
| --- | --- |
| Trong CASE A, hai slot 3 và 4 cần cân nhắc gì và lúc nào Ma nhãn có giá trị? | Loại Giáp thống khổ theo cấu hình cá nhân, giữ ngoại lệ đồ trợ thủ. So sánh rủi ro vật lý/chí mạng/xuyên giáp và phép/cấu rỉa theo quan sát. Ma nhãn phải bao phủ đúng góc vòng và cửa sổ tàng hình. |
| Trong CASE B, Phù chú trường sinh và Khiên Thánh Quang thay đổi cơ hội sống theo cách nào? | Nêu ứng viên hồi định kỳ và điều kiện ngừng chịu đòn, đối chiếu khiên sau khi gây sát thương lên tướng. Xét cả sát thương chuẩn theo máu mục tiêu, xuyên giáp, chí mạng và phép. Coi lựa chọn của người chơi là kinh nghiệm. |
| Khi Allain đang tiến gần ngưỡng hồi, Áo choàng Ra và Khiên thất truyền tác động vào thời điểm nào? | Nêu điều kiện áp hiệu ứng riêng, phân biệt giảm hồi và giảm tốc đánh, giữ trạng thái ứng viên. |
| Long tướng và Long Hống hồi theo điều kiện nào? | Phân biệt hồi theo lượt tham gia hạ tướng và hút máu, giữ trạng thái hệ số đang chờ xác minh. |
| Bolt Baron đánh thường và dùng Thiên lôi bộ gây sát thương thuộc loại nào? | Cả hai có thành phần phép. Phân biệt đòn đánh và kỹ năng. Bản vá hiển thị không sửa hệ số. |
| Hayate tích ba đòn trên mỗi mục tiêu trong hai mục tiêu có kích hoạt sát thương chuẩn không? | Cần sáu lần trúng cùng mục tiêu. Cửa sổ bốn giây tính sau khi kích hoạt. |
| Khi nào Omen có thể cắt hồi chiêu và ép cánh? | Gắn chuỗi đánh trúng với trạng thái cường hóa, thời lượng miễn thương của chiêu riêng, đường rút và nhịp mục tiêu. |
| Florentino hoặc build xuyên giáp mạnh có đủ lý do để chốt Phù chú slot cuối không? | Tách xuyên giáp và sát thương chuẩn, chọn theo nhịp ngân sách, nguồn sát thương và bảo kê. |
| Vì sao Tê Cóng có hai mốc 10 và 45 giây? | Phân biệt giãn cách sử dụng và thời gian hồi một lượt. |
| Hồ sơ Thane SP có áp dụng cho Richter SP không? | Tra profile theo ID và vai trò. Hồ sơ chỉ áp dụng cho Thane ở vị trí hỗ trợ. |
| Khi nào có thể xác nhận giá, công thức ghép và màu icon? | Chỉ xác nhận từng thuộc tính có bằng chứng. Nêu rõ ngày hiệu lực của danh mục, công thức hoặc màu nếu còn thiếu. |

Kiểm thử tự động rà dữ liệu nền, truy xuất và điều kiện. Điểm đánh giá tác nhân chỉ ghi sau khi thực sự chạy mô hình với các câu hỏi trên.

## Ca xem lại trận Thane SP và Yena

Quan sát từ replay tiếng Việt do người chơi cung cấp. Thane và Yena thuộc đội đỏ. Đội đỏ phá nhà chính xanh, tỷ số **10–24** theo thứ tự xanh–đỏ. Các mốc dưới đây theo đồng hồ trận.

| Mốc trận | Diễn biến nhìn thấy | Nhận định chiến thuật |
| --- | --- | --- |
| 01:00–01:17 | Thane bị ép ở cửa rừng, lùi về trụ với ít máu rồi bị hạ. | Rời cửa rừng sớm khi nhiều địch áp sát. Giữ đẩy lùi để cắt đường truy đuổi nếu cần. |
| 02:00–02:13 | Rồng xuất hiện. Thane vào giao tranh ở cửa hang khi đồng đội ở gần, tham gia hạ gục rồi lùi. | Kiểm tra người theo và lối rút trước khi lên. |
| 07:09–07:13 | Thane thấp máu, biến về sát vách sau trụ và bị cắt từ hướng bụi. | Lùi thêm khỏi tầm áp sát rồi mới biến về. |
| 08:28–08:46 | Thane thấp máu, chiêu cuối đang hồi, đi men hang Caesar trở lại giao tranh rồi bị hạ. Banner sau đó ghi Yena hạ liên tiếp hai tướng xanh. | Nếu đã tách được và còn lối rút, chốt rút. Khi đánh giá Yena, ghi nhận hai mạng ở pha này và đối chiếu với đội thắng trước khi quy trách nhiệm. |
| Khoảng 05:50 và 10:50 | Thấy lần lượt icon khớp Giày kiên cường và Khiên Thánh Quang trên thanh đồ Thane. | So đường ghép ở thời điểm giao tranh thực tế. Mốc nhìn thấy icon chưa đủ để xác định thời điểm mua hoặc giá. |

Chân dung Yena đối chiếu với [hồ sơ Garena](https://lienquan.garena.vn/hoc-vien/tuong-skin/d/yena/). Replay chủ yếu bám Thane và không đủ để chấm hiệu quả của Yena trong cả trận hoặc xác nhận giá, hệ số kỹ năng và phiên bản máy chủ.
