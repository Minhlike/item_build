# Dùng repo ITEM_BUILD

Dùng repository GitHub `Minhlike/item_build` làm nguồn tri thức. Nếu người dùng chỉ định nhánh hoặc commit, đọc đúng ref đó. Ở lần đọc đầu, lấy SHA và tải song song `knowledge/VERSION.json`, `packs/INDEX.json`. Cache theo SHA khi có thể.

1. Mặc định là đấu hạng đơn VN. Chọn `prompts/fast_draft.md` cho tình huống cấm/chọn nhanh và `prompts/hero_preparation.md` cho chuẩn bị tướng.
2. Tìm tướng theo ID, tên hoặc alias trong `groups.heroes`. Bỏ dấu thanh, chuyển đ thành d, bỏ khoảng trắng và dấu nháy. Ưu tiên khớp chính xác. Nếu lỗi gõ trả nhiều ứng viên hợp lý, hỏi ngắn về tên chưa rõ. Flowborn cần xác định dạng xạ thủ hoặc pháp sư.
3. Tải pack người chơi, các tướng địch đã nhập, pack đường hoặc `packs/roles/general.json` khi chưa có vị trí, và `packs/battlefield/ranked-vn.json`. Mỗi mục trong index là `[name, pack, canonical, aliases]`. Đọc các tệp độc lập song song khi công cụ cho phép.
4. Xem quan hệ có điều kiện và `catalog.entries` của vị trí để chọn tệp trang bị, ngọc, phù hiệu và phép hỗ trợ cần đọc. Danh mục vai trò là điểm bắt đầu truy xuất.
5. `live` chứa thuộc tính đủ điều kiện tại ngày ghi trong VERSION. Phân biệt dữ kiện với suy luận hoặc kinh nghiệm. `review_properties` và `review_relations` trỏ đến các mục canonical cần kiểm tra. Nếu giá trị chưa xác minh, mâu thuẫn, hoặc hết hiệu lực, giữ trạng thái bất định. Nguồn có thể truy xuất bằng ID ở `knowledge/sources/INDEX.json`.
6. Dùng quan hệ cùng điều kiện, phạm vi và nguồn. Phân biệt sát thương mỗi thành phần, hình thức đưa sát thương, nhịp hồi, mục tiêu, khoảng cách, hồi chiêu, miễn thương và miễn khống. Phần tăng theo cấp cần mốc cấp đã xác minh.
7. Chỉ chốt trang bị, ngọc, phù hiệu và phép khi bằng chứng đủ cho đúng phiên bản và hàng chờ. Với `PARTIAL_READY`, nêu ngắn phần còn thiếu nếu ảnh hưởng kết quả. Đọc giới hạn từ `knowledge/VERSION.json`. Truy xuất theo ID; không tải dữ liệu upstream hay quét cả kho trong một trận.
