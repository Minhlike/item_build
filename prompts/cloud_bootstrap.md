# Dùng repo ITEM_BUILD

Dùng repository GitHub `Minhlike/item_build` làm nguồn tri thức. Nếu người dùng chỉ định nhánh hoặc commit, đọc đúng ref đó. Lấy SHA và đọc `knowledge/VERSION.json` cùng chỉ mục của tầng đang dùng. Cache theo SHA khi có thể.

## L1 dành cho cấm/chọn nhanh

1. Đọc `packs/l1/INDEX.json` và `prompts/fast_draft.md` tại cùng SHA. Chuẩn hóa ID, tên và alias từ `heroes`. Nếu tên chưa rõ, hỏi ngắn. Flowborn cần xác định dạng pháp sư hoặc xạ thủ.
2. Dùng đường dẫn trong L1 để lấy file chiến trường, vai trò, tướng người chơi và các tướng địch hoặc đồng minh đã nhập. Chỉ mở `team/<id>.json` khi toàn bộ tướng trong mục tương ứng của `team_threats` có trong đội địch. Giữ đúng điều kiện áp dụng và lọc macro theo `hero` khi có.
3. Dùng `shortlist` để tìm các món theo vai trò. Áp `preferences` và `personal_filter` khi đúng ID và vai trò. Khi thiếu phương án hợp lệ hoặc cơ chế ảnh hưởng quyết định, mở món tương ứng trong L2.
4. `live` của L1 chứa giá trị đã xác minh. `formula_basis` giữ loại biến cho cơ chế có công thức. Đọc `l2` để lấy hệ số, mốc cấp, nguồn theo thuộc tính và nội dung ứng viên. Đọc L2 trước khi tính hoặc kết luận dựa vào thuộc tính chỉ có trong `review`. Khi cần lịch sử, lấy `canonical` từ L2 và tra ID nguồn theo `evidence` trong chỉ mục.

## L2 và L3

Đọc `packs/INDEX.json` tại cùng SHA. L2 ưu tiên các pack theo ID và nhóm cần thiết. L3 dùng canonical ở `knowledge/` và các mục liên quan trong chỉ mục nguồn. Nếu connector trả nguyên file, ưu tiên lấy trực tiếp thuộc tính qua đường dẫn đã biết.

1. Mặc định là đấu hạng đơn VN. Chọn `prompts/hero_preparation.md` cho chuẩn bị tướng. Đọc `prompts/reasoning_protocol.md` khi cần đối chiếu mốc vàng, công thức hoặc độ nhạy.
2. Tìm tướng theo ID, tên hoặc alias trong `groups.heroes`. Bỏ dấu thanh, chuyển đ thành d, bỏ khoảng trắng và dấu nháy. Ưu tiên khớp chính xác. Nếu lỗi gõ trả nhiều ứng viên hợp lý, hỏi ngắn về tên chưa rõ. Flowborn cần xác định dạng xạ thủ hoặc pháp sư.
3. Tải pack người chơi, các tướng địch đã nhập, pack đường hoặc `packs/roles/general.json` khi chưa có vị trí, và `packs/battlefield/ranked-vn.json`. Mỗi mục trong index là `[name, pack, canonical, aliases]`. Đọc các tệp độc lập song song khi công cụ cho phép.
4. Mở các nhóm phù hợp ở `catalogs` trong index. Với hỗ trợ, bắt đầu từ `defense`, `support`, `boots`. Với chuẩn bị tướng, thêm `runes`, `enchantments` và `spells`. Mở thêm nhóm vật lý, phép hoặc rừng khi build/tướng cần. `catalog.entries` trong pack đường cũ chỉ là ví dụ. ID của mọi món đã biên tập đều có trong pack nhóm, kể cả món thành phần và ứng viên cần kiểm chứng. Dùng bảng `groups` của index để tìm canonical theo ID.
5. `live` chứa thuộc tính đủ điều kiện tại ngày ghi trong VERSION. `candidates` và `candidate_relations` mang trạng thái UNVERIFIED cùng lớp nguồn. `official_undated_or_unresolved` là mô tả chính thức chưa xác định hiệu lực. `community_or_unverified` cần nguồn mạnh hơn. `inference` là diễn giải hoặc kinh nghiệm. `conflict` là mâu thuẫn chưa giải quyết. Tra ID nguồn ở `knowledge/sources/INDEX.json` và lịch sử trong canonical. Nhãn LIVE_VN áp dụng từng thuộc tính. Ví dụ, một món có cơ chế có ngày vẫn có thể thiếu giá hoặc tình trạng bán trong client.
6. Đọc `preferences` chỉ khi khớp đúng ID người chơi và vị trí. Áp giới hạn cá nhân trước khi so sánh phương án. Với Thane hỗ trợ, loại Giáp thống khổ; loại món ngoài nhóm hỗ trợ nếu `activation` là `manual` hoặc `mixed`. Chờ xác minh trước khi chọn món ngoài nhóm hỗ trợ có thao tác `unknown`. `automatic` là tự kích hoạt khi thỏa điều kiện. `stats_only` là chỉ số trực tiếp theo hồ sơ.
7. Dùng quan hệ theo điều kiện, phạm vi và nguồn. So theo mốc vàng, thời gian tiếp xúc, loại sát thương, cơ sở HP và khả năng kích hoạt dựa trên trạng thái quan sát được. Phần tăng theo cấp cần mốc cấp đã xác minh. Xem ứng viên khi cần lập giả thuyết hoặc so sánh có điều kiện, đồng thời giữ rõ ký hiệu và giới hạn bằng chứng.
8. Chỉ chốt trang bị, ngọc, phù hiệu và phép khi bằng chứng đủ cho đúng phiên bản và hàng chờ. Với PARTIAL_READY, nêu ngắn khoảng trống ảnh hưởng kết quả. Truy xuất theo ID và nhóm nhỏ, giữ cùng SHA. Snapshot upstream cục bộ không nằm trong GitHub.

Với đối chiếu đội hình, lộ trình mua hoặc chiến thuật theo thời điểm, áp dụng `prompts/reasoning_protocol.md` cùng SHA. `tactics` trong index trỏ tới các mẫu có điều kiện và neo thuộc tính. Đọc đồng minh khi người chơi đã nhập. Giữ định dạng đầu ra của chế độ đã chọn.
