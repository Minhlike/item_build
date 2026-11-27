# Kiểm định độc lập Phase 3

56 tình huống bao phủ năm vị trí, sáu lớp tướng và tám chiều chấm. `questions.tsv` dùng để tạo gói đề. `rubric.tsv` chứa tiêu chí, đáp án và liên kết bằng ID cho người chấm. Nội dung câu hỏi và chỉ dẫn chung giống nhau ở A/B/C.

```powershell
uv run --locked python evaluations/phase3/run.py validate
uv run --locked python evaluations/phase3/run.py prepare --out .local/eval/run-001 --model <model-id> --settings .local/eval/settings.json --phase3 <commit-sha>
uv run --locked python evaluations/phase3/run.py score --out .local/eval/run-001
```

`settings.json` là đối tượng JSON ghi cấu hình thực tế dùng chung. Lưu ID bản mô hình, số token tối đa, chế độ suy luận, tham số lấy mẫu/seed nếu được hỗ trợ và cấu hình công cụ cho ba nhánh. Ghi `null` khi nhà cung cấp không công bố hoặc không cho đặt một tham số. Chạy cả ba nhánh cùng bề mặt và cùng thời điểm đủ gần để hạn chế thay đổi bản mô hình.

- **Người chạy.** Theo thứ tự ngẫu nhiên trong `manifest.json`, mỗi lượt dùng phiên mới. Cấp đúng nội dung `packets/<trial>.json` ở vai trò system và user tương ứng. Cho công cụ đọc đúng một gói đã giải nén theo manifest. A trống, B ghim b0146c9, C ghim commit Phase 3. Nếu có quyền dùng CLI, root chỉ định phải là gói đã giải nén và chỉ dùng các lệnh tra cứu/tính toán có trong bản đó. Cùng hạn mức đọc/đầu ra cho mọi nhánh. Tắt nguồn ngoài, bộ nhớ và công cụ tra repo tổng. Không cấp quyền đọc `evaluations`, manifest, bài trả lời khác hoặc rubric cho mô hình.
- **Người chấm.** Lưu phản hồi thực tế vào `responses/<trial>.txt`. Chấm mù theo `grading.tsv`, câu hỏi và rubric, không nhận cột nhánh. Ghi hai cột `trial`, `score` vào `scores.tsv`. Chấm 2 khi thỏa cả hai tiêu chí, 1 khi thỏa một tiêu chí và không có sai sót làm hỏng kết luận, 0 khi thiếu ý chính hoặc có lỗi ảnh hưởng quyết định. Chấp nhận kết luận tương đương có cùng điều kiện. Không ghi điểm cho lượt chưa chạy.
- **Đối chiếu.** Báo cáo nhóm chỉ dùng bộ ba A/B/C có đủ bài và điểm. Lưu thời điểm, số token vào/ra, số lượt truy xuất thực tế và mã phiên nếu nhà cung cấp trả về. Nếu một nhánh thiếu phản hồi, bộ ba đó chưa được so sánh. Chất lượng chỉ đo trên phạm vi bộ đề này.

Harness tạo gói offline và tổng hợp điểm đã nhập. Việc gọi mô hình cần bề mặt được phép và được thực hiện bên ngoài harness. Để chấm mù đúng nghĩa, giao `grading.tsv` và bản ghi phản hồi cho người chấm riêng.
