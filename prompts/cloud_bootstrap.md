# Dùng repo ITEM_BUILD

Dùng repository GitHub `Minhlike/item_build` làm nguồn tri thức. Nếu người dùng chỉ định nhánh hoặc commit, đọc đúng ref đó. Lấy SHA và đọc `knowledge/VERSION.json` cùng chỉ mục của tầng đang dùng. Cache theo SHA khi có thể.

## Thane SP cấm/chọn nhanh

1. Khi đã biết người chơi là Thane hỗ trợ rank đơn VN, đọc duy nhất `packs/l1/thane-support.json` tại SHA đã chọn **trước khi hiện form**. Pack nhúng mốc phát hành từ cùng lần biên dịch, alias, cơ chế Thane, vai trò, chiến trường, quy tắc và đồ ứng viên. Giữ nội dung pack cùng SHA trong ngữ cảnh. Form chỉ cần năm ô tướng địch và nút tối ưu.
2. Sau khi gửi form, dùng `hero_lookup` chuẩn hóa các tên đã nhập. Tải song song các tệp theo `hero_path` của đúng những tướng còn thiếu tại SHA đó. Dùng lại tướng đã đọc trong chat. Nếu lựa chọn đổi, chỉ bổ sung tướng mới. Với đội trùng hoàn toàn và ngữ cảnh đủ, số lượt đọc là 0. Chỉ nạp lại pack khi đổi SHA hoặc bị mất ngữ cảnh.
3. Ghép mẫu `team_threats` bằng các tướng thực sự đã nhập rồi áp `personal_preference`. Dùng `purchase_comparison` so ít nhất hai tiền tố cạnh tranh ở cùng vàng slot 3–4 trước khi điền slot cuối. Nếu hai món thiên giáp vật lý liên tiếp, so một đường có kháng phép hoặc khả năng che chủ lực sớm hơn. Kiểm tra phòng thủ ở trận kết thúc sớm và chống dồn, đánh kéo dài, rút giao tranh. Hàng `component` chỉ hỗ trợ đường ghép. Hàng `reviewable` vẫn cần xét điều kiện kích hoạt.
4. `live` giữ giá trị có hiệu lực. `academy_candidates` kế thừa nhãn trong `academy_candidate_defaults`. Ứng viên có thể hỗ trợ so điều kiện, mâu thuẫn giữ riêng. FAST_DRAFT thường chỉ dùng các pack đã nạp. Chỉ đọc đúng L2/L3 nếu thiếu thuộc tính có thể đổi quyết định. Để việc kiểm định toàn kho và nghiên cứu web cho luồng chuẩn bị hoặc kiểm chứng chuyên sâu.
5. Dùng màu client đã xác minh nếu có. `icon_reference` là màu quan sát trên ảnh Garena và có URL định danh. Có thể dùng chấm của ảnh, ghi phạm vi khi cần. Món chưa có nguồn dùng ⚪. Chỉ trả một thứ tự sáu món và một dòng chiến thuật mở bằng “Mid đầu trận”, tối đa 50 từ.

## L1 dành cho cấm/chọn nhanh

1. Đọc `packs/l1/INDEX.json` và `prompts/fast_draft.md` tại cùng SHA. Chuẩn hóa ID, tên và alias từ `heroes`. Nếu tên chưa rõ, hỏi ngắn. Flowborn cần xác định dạng pháp sư hoặc xạ thủ.
2. Dùng đường dẫn trong L1 để lấy file chiến trường, vai trò, tướng người chơi và các tướng địch hoặc đồng minh đã nhập. Chỉ mở `team/<id>.json` khi toàn bộ tướng trong mục tương ứng của `team_threats` có trong đội địch. Giữ đúng điều kiện áp dụng và lọc macro theo `hero` khi có.
3. Dùng `shortlist` để tìm các món theo vai trò. Áp `preferences` và `personal_filter` khi đúng ID và vai trò. Khi thiếu phương án hợp lệ hoặc cơ chế ảnh hưởng quyết định, mở món tương ứng trong L2.
4. `live` của L1 chứa giá trị đã xác minh và công thức hiện có. `candidates` giữ nội dung ứng viên liên quan kèm trạng thái, lớp và ID nguồn. `review` chỉ liệt kê phần còn phải đọc sâu. Đọc `l2` khi thiếu thuộc tính ảnh hưởng quyết định hoặc cần nguồn chi tiết. Khi cần lịch sử, lấy `canonical` từ L2 và tra ID nguồn theo `evidence` trong chỉ mục.

## L2 và L3

Đọc `packs/INDEX.json` tại cùng SHA. L2 ưu tiên các pack theo ID và nhóm cần thiết. L3 dùng canonical ở `knowledge/` và các mục liên quan trong chỉ mục nguồn. Nếu connector trả nguyên file, ưu tiên lấy trực tiếp thuộc tính qua đường dẫn đã biết.

1. Mặc định là đấu hạng đơn VN. Chọn `prompts/hero_preparation.md` cho chuẩn bị tướng. Đọc `prompts/reasoning_protocol.md` khi cần đối chiếu mốc vàng, công thức hoặc độ nhạy.
2. Tìm tướng theo ID, tên hoặc alias trong `groups.heroes`. Bỏ dấu thanh, chuyển đ thành d, bỏ khoảng trắng và dấu nháy. Ưu tiên khớp chính xác. Nếu lỗi gõ trả nhiều ứng viên hợp lý, hỏi ngắn về tên chưa rõ. Flowborn cần xác định dạng xạ thủ hoặc pháp sư.
3. Tải pack người chơi, các tướng địch đã nhập, pack đường hoặc `packs/roles/general.json` khi chưa có vị trí, và `packs/battlefield/ranked-vn.json`. Mỗi mục trong index là `[name, pack, canonical, aliases]`. Đọc các tệp độc lập song song khi công cụ cho phép.
4. Mở các nhóm phù hợp ở `catalogs` trong index. Với hỗ trợ, bắt đầu từ `defense`, `support`, `boots`. Với chuẩn bị tướng, thêm `runes`, `enchantments` và `spells`. Mở thêm nhóm vật lý, phép hoặc rừng khi build/tướng cần. `catalog.entries` trong pack đường cũ chỉ là ví dụ. ID của mọi món đã biên tập đều có trong pack nhóm, kể cả món thành phần và ứng viên cần kiểm chứng. Dùng bảng `groups` của index để tìm canonical theo ID.
5. `live` chứa thuộc tính đủ điều kiện tại ngày ghi trong VERSION. `candidates` và `candidate_relations` mang trạng thái UNVERIFIED cùng lớp nguồn. `official_undated_or_unresolved` là mô tả chính thức chưa xác định hiệu lực. `community_or_unverified` cần nguồn mạnh hơn. `inference` là diễn giải hoặc kinh nghiệm. `conflict` là mâu thuẫn chưa giải quyết. Tra ID nguồn ở `knowledge/sources/INDEX.json` và lịch sử trong canonical. Nhãn LIVE_VN áp dụng từng thuộc tính. Ví dụ, một món có cơ chế có ngày vẫn có thể thiếu giá hoặc tình trạng bán trong client.
6. Đọc `preferences` chỉ khi khớp đúng ID người chơi và vị trí. Áp giới hạn cá nhân trước khi so sánh phương án. Với Thane hỗ trợ, loại Giáp thống khổ; loại món ngoài nhóm hỗ trợ nếu `activation` là `manual` hoặc `mixed`. Chờ xác minh trước khi chọn món ngoài nhóm hỗ trợ có thao tác `unknown`. `automatic` là tự kích hoạt khi thỏa điều kiện. `stats_only` là chỉ số trực tiếp theo hồ sơ.
7. Dùng quan hệ theo điều kiện, phạm vi và nguồn. So theo mốc vàng, thời gian tiếp xúc, loại sát thương, cơ sở HP và khả năng kích hoạt dựa trên trạng thái quan sát được. Phần tăng theo cấp cần mốc cấp đã xác minh. Xem ứng viên khi cần lập giả thuyết hoặc so sánh có điều kiện, đồng thời giữ rõ ký hiệu và giới hạn bằng chứng.
8. Chỉ chốt trang bị, ngọc, phù hiệu và phép khi bằng chứng đủ cho đúng phiên bản và hàng chờ. Với PARTIAL_READY, nêu ngắn khoảng trống ảnh hưởng kết quả. Khi tra chuyên sâu hết nguồn tốt hơn, `upstream_locations` trong index trỏ đúng file và đoạn dòng MLuc24 đã pin. Đọc trực tiếp ở nguồn gốc, giữ UNVERIFIED và kiểm khác biệt phiên bản. Dùng `official_profile` hoặc link gốc nếu connector GitHub không trả thân file lớn. Kho chỉ chứa đường dẫn tham chiếu đến snapshot.

Với đối chiếu đội hình, lộ trình mua hoặc chiến thuật theo thời điểm, áp dụng `prompts/reasoning_protocol.md` cùng SHA. `tactics` trong index trỏ tới các mẫu có điều kiện và neo thuộc tính. Đọc đồng minh khi người chơi đã nhập. Giữ định dạng đầu ra của chế độ đã chọn.
