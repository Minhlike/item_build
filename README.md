# ITEM_BUILD

Kho tri thức Liên Quân Mobile Việt Nam cho tác nhân có thể đọc GitHub. Phiên bản tham chiếu hiện tại là **Vết Nứt Thời Không, cập nhật ngày 26/11/2026**. Mức sử dụng là **PARTIAL_READY**. Có thể tra danh tính, bằng chứng cơ chế đã kiểm chứng và ghi chú cân bằng theo thuộc tính. Những khoảng trống còn lại ảnh hưởng trực tiếp đến khả năng chốt đủ sáu trang bị hoặc bảng ngọc và phù hiệu hợp lệ. [Thông báo Garena](https://lienquan.garena.vn/dieu-chinh-giua-mua-pb-vet-nut-thoi-khong-26-11-2026/)

## Đọc trên ChatGPT Cloud

Mở kho ở nhánh hoặc commit chứa dữ liệu, đưa nội dung `prompts/cloud_bootstrap.md` cho tác nhân và cung cấp tên tướng, vị trí nếu biết, cùng tối đa năm tướng địch. Đọc `knowledge/VERSION.json` và `packs/INDEX.json` để tra đường dẫn trực tiếp. Khi có thể, ghim tất cả lượt đọc vào cùng một SHA. Các pack là JSON UTF-8, có thể đọc trực tiếp trên GitHub.

Ví dụ đầu vào

```text
FAST_DRAFT | Thane hỗ trợ | Đội địch: TV, BB, Allain, Natalya, Ryoma
HERO_PREPARATION | Hayate đường Rồng
```

## Chạy cục bộ

Yêu cầu Git, Python 3.12 và uv. Trên WSL, dùng một môi trường uv riêng khi làm việc chung thư mục với Windows, chẳng hạn `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/item-build-wsl-venv"`.

```sh
uv sync --locked
uv run item-build audit
uv run item-build enrich --hero thane
uv run item-build query --hero "trieu van" --canonical
uv run item-build query --hero edras --local-upstream
uv run item-build context --hero thane --role support --enemies "trieu van" "bolt baron" allain natalya ryoma
uv run item-build context --hero thane --role support --enemies arthur violet natalya ryoma quillen --include-candidates
uv run item-build context --mode hero_preparation --hero hayate --role dragon
uv run item-build cooldown --entity spells/dich-chuyen --property active.teleport
uv run item-build compile
uv run item-build validate
uv run pytest -q
uv run item-build benchmark
uv run item-build benchmark --catalogs
```

`ingest` kiểm tra SHA pin, tái sử dụng Git object đã tải, lưu blob gốc và manifest SHA-256 ở `.local/raw/`, rồi tạo bản rà soát ở `.local/clean/` và `.local/review/<SHA>/`. Bản rà soát theo tướng giữ toàn văn từng kỹ năng kèm vị trí cụm cơ chế và trị số tìm thấy. Các cụm dò được dùng để tìm đoạn cần đọc. `audit` tính lại báo cáo từ toàn bộ nguồn. `enrich` liệt kê dữ liệu thiếu, thuộc tính chờ thẩm định và gợi ý truy vấn theo bốn ngôn ngữ. `query --local-upstream` đọc hồ sơ cục bộ sau khi chạy ingest, với nhãn `local_unverified`.

`context` lấy các pack liên quan cho tác nhân phân tích. Thêm `--include-candidates` để đưa vào dữ kiện chưa có mốc hiệu lực, suy luận và mâu thuẫn, kèm nguồn. `catalogs` trong index trỏ tới các pack nhóm đã biên dịch, gồm cả đồ thành phần. Khi có ID tướng và vị trí trùng khớp, `preferences` trỏ tới hồ sơ cá nhân. `cooldown` đọc hồi chiêu cơ bản đã xác minh, phân biệt thời gian hồi lượt với hồi chiêu và từ chối tính theo cấp khi thiếu mốc cấp. Cặp `--cdr` và `--cap` mô phỏng riêng công thức giảm hồi chiêu chuẩn theo giả định nhập vào. Reset, giảm thời gian hồi còn lại và hồi lượt được biểu diễn theo từng cơ chế.

## Dữ liệu và quyền nguồn

| Tầng | Đường dẫn | Nội dung |
| --- | --- | --- |
| Raw | `.local/raw/` | Blob không sửa đổi, commit nguồn, thời gian lấy và checksum |
| Clean | `.local/clean/` | Bỏ hình ảnh và nội dung trang trí, giữ mô tả và điều kiện để rà soát |
| Cơ chế và ngữ cảnh | `sources/`, `patches/`, `overrides/` | Sự kiện độc lập, lịch sử thuộc tính, quan hệ có điều kiện và bằng chứng |
| Canonical | `knowledge/` | Hồ sơ đầy đủ theo ID và đồ thị JSON có kiểu |
| Packs | `packs/` | LIVE_VN, ứng viên có lớp bằng chứng, pack nhóm và đường dẫn tới canonical |
| Truy xuất | `packs/INDEX.json`, CLI | Tra ID, alias và lỗi chính tả bằng chỉ mục trong RAM |

Khóa `kind` mặc định là `mechanical_fact`; khóa `status` mặc định là `UNVERIFIED` ở hồ sơ gốc. Các thuộc tính tình huống dùng `derived_knowledge`, `behavioral_tendency` hoặc `tactical_heuristic`. Thiếu giá trị là thiếu dữ liệu. Công thức dùng AST tuyến tính gồm gốc, hệ số và cơ sở có kiểu. `origin` là mốc cấp để tính phần tăng trưởng; nếu vắng, bảng chi tiết giữ nguyên số liệu công bố và CLI yêu cầu xác minh mốc trước khi tính. `unspecified_ad` giữ nguyên bất định giữa công cơ bản, cộng thêm và tổng.

Registry tại `knowledge/sources/registry.json` lưu phạm vi khai thác và phân phối. Dữ liệu upstream được giữ cục bộ. Giấy phép MIT của upstream áp dụng cho crawler và script hợp nhất. Bản phát hành công khai dùng định danh, dữ kiện độc lập đã biên tập, dẫn nguồn và số liệu kiểm định tổng hợp. [LICENSE tại SHA đã kiểm định](https://github.com/MLuc24/lien-quan-data/blob/a210fe47690de7cefd18f76b61694724e02fdb5e/LICENSE)

## Cập nhật và khôi phục

1. Chạy `uv run item-build update` để kiểm tra HEAD upstream, kiểm tra các URL có quyền theo dõi đã đăng ký và biên dịch lại. Thông báo Garena được rà qua trang [Cập nhật](https://lienquan.garena.vn/cap-nhat/) do quyền theo dõi tự động chưa được cấp.
2. Ghi tài liệu bằng chứng vào `sources/evidence.json`. Thêm bản ghi patch vào `patches/` với máy chủ, ngày hiệu lực, thuộc tính bị đổi, loại thay đổi và giá trị cũ nếu nguồn cung cấp. Giá trị cũ chưa biết ngày bắt đầu vẫn có thể lưu với ngày kết thúc và trạng thái SUPERSEDED.
3. Chỉnh sửa đã thẩm định có thể đặt tại `overrides/` theo hợp đồng patch. Ghi rõ nguồn và ngày áp dụng. Khi phát hiện quan hệ không còn hợp lệ sau sửa cơ chế, cập nhật điều kiện hoặc ngày kết thúc của quan hệ trong `sources/relations.json`.
4. Nếu patch áp dụng lên VN, cập nhật `sources/release.json`, chạy `compile`, `validate` và pytest. Soát diff rồi commit cả thay đổi nguồn và đầu ra sinh lại. Dùng cùng một SHA khi đọc qua GitHub. Pack giữ dữ liệu đúng thời điểm phát hành và mang theo trạng thái nguồn.
5. Khôi phục cả nguồn và đầu ra bằng cách đọc commit phát hành trước, hoặc dùng `git revert <commit>` trên nhánh phát triển rồi kiểm định và review như một bản cập nhật mới.

Theo dõi HTTP chỉ hoạt động với `acquisition: approved_http`, `permission_ref` và `monitor_urls` hợp lệ. Chương trình kiểm tra robots, dùng ETag và Last-Modified, băm nội dung và lưu checkpoint cục bộ. Thay đổi phát hiện được chờ thẩm định trước khi trở thành thuộc tính. [Điều khoản Garena Việt Nam](https://garena.vn/terms)

Xem [bàn giao Phase 2](reports/phase2.md), [kiểm định upstream](reports/upstream-audit.json), [benchmark pack nhóm](reports/catalog-benchmark.json) và [bộ câu hỏi nghiệm thu](evaluations/reasoning.md). [Bàn giao Phase 1](reports/handoff.md) và [benchmark Phase 1](reports/benchmark.json) lưu số liệu tại checkpoint ban đầu.
