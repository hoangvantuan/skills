---
name: meeting-minutes
description: "Tạo biên bản họp hoặc phân tích hành vi giao tiếp từ transcript/ghi chú (decisions, action items, speaking ratio, patterns)."
---

# Meeting Minutes: Biên bản họp & Phân tích giao tiếp

Skill có 2 workflow. Chọn workflow dựa trên yêu cầu user.

## Workflow Routing

| User muốn | Workflow | Output |
|-----------|----------|--------|
| Tạo biên bản, tóm tắt cuộc họp, ghi lại quyết định/action items | **Minutes** | `meeting-minutes/{slug}-{YYMMDD-HHmm}.md` |
| Phân tích hành vi giao tiếp, nhận diện pattern, cải thiện kỹ năng | **Insights** | `meeting-insights/{slug}-{YYMMDD-HHmm}.md` |

Nếu không rõ, hỏi user bằng AskUserQuestion:
- "Tạo biên bản họp" (Minutes)
- "Phân tích hành vi giao tiếp" (Insights)

## Workflow 1: Minutes (Tạo biên bản họp)

### Bước 1: Tiếp nhận nội dung

1. Nhận input từ user: text trực tiếp hoặc file path
2. Hỗ trợ đọc file: `.txt`, `.md`, `.pdf`, `.docx`, `.vtt`, `.srt`
3. Nếu input là file, đọc nội dung bằng Read tool (PDF dùng tham số `pages` cho file lớn)
4. Scan nhanh nội dung: xác định ngôn ngữ gốc, độ dài, số người tham gia ước lượng
5. Nếu input là transcript, đọc lướt vài đoạn đầu, giữa, cuối trước khi viết. Transcript **không dùng được** khi câu chữ vô nghĩa hoặc lẫn ngôn ngữ không khớp nội dung họp (ví dụ họp tiếng Việt mà ra câu kiểu "Ohh, chính, I think he would"), hoặc quá ít chữ so với thời lượng họp. Khi đó dừng lại, nói rõ dấu hiệu thấy được và đề nghị user cung cấp transcript tốt hơn. Không viết biên bản từ transcript kém, vì quyết định và action item rút ra từ đó sẽ sai mà không ai nhận ra.

### Bước 2: Hỏi bổ sung (tối đa 3 câu)

**Chỉ hỏi khi thông tin KHÔNG thể suy ra từ nội dung.** Nếu transcript/ghi chú đã chứa đủ metadata, bỏ qua bước này.

Các thông tin cần xác nhận (nếu thiếu):

1. Tên cuộc họp, ngày, thời gian bắt đầu (hoặc thời lượng), người tổ chức?
2. Có agenda hoặc tài liệu bổ sung nào không?
3. Ai duyệt biên bản?

Nếu user trả lời "không có transcript" hoặc "không có agenda", đánh dấu nguồn là "ghi chú ad-hoc" và ghi chú những chỗ có thể thiếu thông tin.

### Bước 3: Tạo biên bản

Tạo biên bản theo cấu trúc chuẩn. Tham khảo chi tiết tại `references/minutes-schema.md`.

Quy tắc xử lý:

- **Trích xuất quyết định**: tìm các cụm "đồng ý", "quyết định", "thống nhất", "approved", "decided", "agreed" trong nội dung
- **Trích xuất action items**: tìm các cụm "sẽ làm", "phụ trách", "deadline", "trước ngày", "assigned to", "action", "TODO", "task"
- **Suy luận owner**: nếu nội dung nói "Minh sẽ xử lý", owner = Minh
- **Người nói ẩn danh**: nếu transcript chỉ có nhãn chung chung như `Speaker 1`, `Speaker 2` hoặc `@1`, `@2`, không gán owner theo nhãn đó và không đoán tên từ giọng điệu hay nội dung. Ghi owner là "Chưa xác định owner", trừ khi chính câu nói nêu tên người nhận việc ("anh Minh lo phần này")
- **Suy luận deadline**: nếu nội dung nói "xong trước thứ 6", tính ngày cụ thể từ ngày họp
- **Trích xuất pending / parking lot**: các hạng mục có thảo luận nhưng chưa có quyết định hay action chính thức, hoặc bị hoãn lại. Ví dụ: "đang cân nhắc", "sẽ bàn thêm", "chưa kết luận", "để sprint sau"
- Mỗi action item cần owner và deadline, vì thiếu thì không ai follow-up được. Nếu không suy ra được, ghi "Cần xác nhận"
- Thông tin không chắc chắn ghi `TBD` kèm ghi chú cần lấy từ đâu
- Metadata chỉ hiển thị thông tin có sẵn hoặc suy ra được. Không liệt kê field với giá trị TBD nếu field đó không quan trọng (ví dụ: "Gửi cho", "Địa điểm"). Chỉ dùng TBD cho thông tin quan trọng cần bổ sung sau

### Bước 4: Lưu và trình bày

1. Tạo thư mục `meeting-minutes/` nếu chưa có
2. Tạo slug từ tên cuộc họp: lowercase, bỏ dấu, thay khoảng trắng bằng `-`, bỏ ký tự đặc biệt (ví dụ: "Sprint Planning Q2" → `sprint-planning-q2`)
3. Lưu biên bản vào file `{slug}-{YYMMDD-HHmm}.md`
4. Hiển thị tóm tắt cho user: số quyết định, số action items, những chỗ cần xác nhận

### Nguyên tắc chất lượng (Minutes)

- Ngắn gọn: họp ≤30 phút thì biên bản ≤1 trang A4, họp ≤60 phút thì ≤2 trang
- Dùng ngôn ngữ đơn giản, bullet list cho dễ đọc
- Ưu tiên quyết định và action items lên đầu
- Ngày tháng dùng ISO 8601 (YYYY-MM-DD)
- Giữ sự thật, tách bạch ý kiến cá nhân (nếu có, đánh dấu rõ "Ý kiến")

## Workflow 2: Insights (Phân tích hành vi giao tiếp)

Phân tích transcript để nhận diện pattern giao tiếp, điểm mạnh, và cơ hội cải thiện. Tham khảo chi tiết tại `references/insights-patterns.md`.

### Bước 1: Thu thập dữ liệu

1. Scan folder hoặc nhận file từ user: `.txt`, `.md`, `.pdf`, `.docx`, `.vtt`, `.srt`
2. Kiểm tra file có speaker labels và timestamps không
3. Xác định khoảng thời gian và số lượng cuộc họp
4. Hỏi user: "Tên/identifier của bạn trong transcript là gì?" (nếu không rõ)

### Bước 2: Xác định mục tiêu phân tích

Nếu user chưa nói rõ, hỏi bằng AskUserQuestion (multiSelect):

- Né tránh xung đột (conflict avoidance)
- Tỉ lệ nói/nghe (speaking ratio)
- Filler words và hedging language
- Kỹ năng lắng nghe chủ động (active listening)
- Phong cách điều hành cuộc họp (facilitation)
- Tất cả các mục trên

### Bước 3: Phân tích patterns

Với mỗi mục tiêu đã chọn, quét toàn bộ transcript. Chi tiết các pattern cần tìm xem tại `references/insights-patterns.md`.

Mỗi pattern tìm được cần:
- Trích dẫn nguyên văn từ transcript (có timestamp nếu có)
- Giải thích tại sao nó quan trọng
- Đề xuất cách làm tốt hơn

### Bước 4: Tổng hợp và lưu kết quả

Tạo báo cáo theo cấu trúc trong `references/insights-patterns.md` (section "Cấu trúc báo cáo output").

1. Tạo thư mục `meeting-insights/` nếu chưa có
2. Lưu vào file `{slug}-{YYMMDD-HHmm}.md`
3. Hiển thị tóm tắt: số patterns tìm được, top 3 điểm mạnh, top 3 cơ hội cải thiện

### Nguyên tắc chất lượng (Insights)

- Mỗi nhận xét phải kèm bằng chứng cụ thể (trích dẫn từ transcript)
- Cân bằng giữa điểm mạnh và cơ hội cải thiện, không chỉ chê
- Đề xuất hành động phải cụ thể, có thể thực hiện ngay
- Khi phân tích nhiều cuộc họp, so sánh xu hướng theo thời gian
- Tôn trọng quyền riêng tư: không phán xét nhân cách, chỉ phân tích hành vi giao tiếp
