# Shun Claude Plugin

Plugin package cho Claude Code — phát triển các **skills**, **agents**, **hooks**, và **MCP servers** mở rộng khả năng của Claude Code.

## Installation

```bash
claude plugin install gh:hoangvantuan/skills
```

## Components

### Skills

| Skill | Description |
| --- | --- |
| `ai-artist` | Tạo ảnh qua Nano Banana, 129 curated prompts, validation interview, 3 modes (search/creative/wild) |
| `anti-ai-writing` | Rules viết tiếng Việt không giống AI, blacklist từ/cụm/chấm câu, self-critique bắt buộc. Dùng độc lập hoặc làm baseline cho mọi task viết |
| `codex-image` | Tạo và chỉnh sửa ảnh 2 chế độ: Codex CLI gpt-image-2 (mặc định, ChatGPT login) + fallback OpenAI API. Text-to-image, nền trong suốt (chroma-key + native gpt-image-1.5), batch, edit (style transfer + mask/high-fidelity), size chính xác tới 4K |
| `creative-thought-partner` | Đối tác tư duy sáng tạo, brainstorming & insight discovery |
| `decision-gate` | Trợ lý phán quyết go/no-go + ưu tiên cho MỘT hạng mục kỹ thuật mơ hồ (bug/feature/techdebt/task). Xác minh bằng chứng read-only trước khi kết luận, chấm điểm theo loại (RICE/ICE/WSJF), xuất decision brief. Luồng 3 pha: Xác minh → Cổng Go/No-Go (checkpoint 1 lần) → Ưu tiên. Dừng ở bản khuyến nghị, không tạo issue/kế hoạch |
| `deep-insight` | Quan sát đa chiều → Phân tích tách lớp → Đúc kết cốt lõi, hiểu sâu vấn đề qua chu trình 3 bước |
| `deep-learner` | Dẫn dắt từng bước hiểu sâu bản chất nội dung, 4 lớp hiểu + áp dụng đời sống |
| `facebook` | Facebook automation via PinchTab, đăng bài lên wall, tag bạn bè |
| `game-theory-lens` | Phân tích chủ đề qua lăng kính Game Theory, nhận diện players/strategies/payoffs, Nash equilibrium, mechanism design |
| `ghost-blog` | Ghost CMS blog management |
| `kinh-dich-lens` | Phân tích tình huống qua Kinh Dịch: 64 Quẻ & Lục Hào, Âm Dương tiêu trưởng, Ngũ Hành cân bằng hệ thống, Biến Thông (Nguyên-Hanh-Lợi-Trinh), Đạo Quân Tử tu dưỡng |
| `m365-shared` | CLI for Microsoft 365: shared patterns — authentication (browser/device code/certificate/secret), installation, output formatting (json + JMESPath), common flags, error handling |
| `m365-calendar` | Outlook calendar qua m365 CLI + Microsoft Graph: đọc lịch theo khoảng thời gian (`calendarView`, bung cả event lặp lại), CRUD calendar, tạo/sửa event, mời người tham dự, họp online Teams, đặt phòng họp (`beta/me/findRooms`), xem rảnh/bận, tìm khung giờ chung, dời một buổi trong chuỗi định kỳ, huỷ/xoá event. Kèm script quy đổi khoảng thời gian neo theo GMT+7 |
| `m365-meeting` | Transcript cuộc họp Teams qua Microsoft Graph và SharePoint: tìm đúng buổi (kể cả họp định kỳ trùng tên, họp mình chỉ tham dự, họp kênh, link `meetingrecap`), kiểm tra ngôn ngữ và chất lượng transcript (đề xuất transcribe lại bằng Soniox khi kém, hỏi trước khi gửi audio), tải transcript, ghi `.txt` có header metadata + `.vtt` gốc. Kèm recording, điểm danh, và preflight tự chẩn đoán 3 bức tường 403 (chưa đăng nhập, thiếu consent, chính sách tenant) kèm câu nhắn IT sẵn. Dừng ở tải file, không tóm tắt (việc của `meeting-minutes`) |
| `m365-teams` | Microsoft Teams management qua m365 CLI: teams, channels, messages (channel + chat), members. Hỗ trợ gửi tin nhắn HTML, chat 1:1/group, quản lý thành viên team/channel |
| `m365-onedrive` | OneDrive personal file management qua m365 CLI: resolve OneDrive URL non-admin (Graph `me/drive`), upload/download/copy/move files, quản lý folder, sharing links, file versions |
| `m365-sharepoint` | SharePoint Online qua m365 CLI — trọng tâm: truy cập/ghi **tài liệu nhóm/Teams** (resolve site qua group, non-admin). Gồm sites, lists, list items (OData + CAML), files (upload/download/checkin/checkout), folders, permissions (users/groups/sharing) |
| `meeting-minutes` | 2 workflow: (1) Tạo biên bản họp từ transcript/ghi chú (quyết định, action items, pending/parking lot), (2) Phân tích hành vi giao tiếp (conflict avoidance, speaking ratio, filler words, active listening, facilitation style) |
| `n8n-cli` | Quản lý n8n instance qua `n8n-cli` (REST API): workflows (CRUD, activate/deactivate, transfer), executions (list/retry/stop), credentials (schema/create), projects, tags, variables, data tables, users, audit. Auto-JSON khi pipe, hỗ trợ `--jq` |
| `nhat-di-quan-chi` | Phân tích vấn đề thực tế bằng tư duy Đông phương tổng hợp (Thu Giang Nguyễn Duy Cần). 4 giai đoạn: Tẩy Tâm → Mổ Xẻ (Dịch Lý) → Định Vị (Thời-Vị-Cơ) → Hành Động (Hoàn Trung, Lưỡng Hành, Vô Vi) |
| `outline-writer` | Phân tích nội dung & tạo outline thuần nội dung (sequence of sections; thesis, key arguments, evidence), không quyết định media (slide/blog/doc), không quy định cách viết/tone/style (đó là việc của writer) |
| `pexels-media` | Source ảnh/video royalty-free từ Pexels API: search, curated, popular, collections, multi-resolution download + sidecar metadata bắt buộc. Cần `PEXELS_API_KEY` |
| `pinchtab` | Browser automation cho AI agents, điều khiển Chrome qua PinchTab HTTP API |
| `planning-content` | Phân tích nội dung & lên outline ý chính cho từng bài. Hỗ trợ mọi input: topic, notes, URL, file (PDF/DOCX/EPUB), YouTube. Convert tài liệu, research, content map, tier processing cho tài liệu lớn. KHÔNG can thiệp cách viết/tone/style |
| `pptx-creator` | Tạo PowerPoint đẹp, chuyên nghiệp, hỗ trợ font tiếng Việt (PptxGenJS) |
| `problem-solving` | Kỹ thuật giải quyết vấn đề có hệ thống, inversion, collision-zone, scale-game, simplification cascades |
| `project-memory` | Bộ nhớ tri thức cấp dự án tự cải tiến. 4 thao tác capture/consolidate/recall/execute, 3 loại entry Tool/Map/Fact với index routing và log timeline. Cơ chế portable trong skill, dữ liệu ghi vào memory/ ở gốc repo. Script Python stdlib giữ index luôn đồng bộ |
| `prompt-engineering` | Prompt engineering patterns: few-shot, chain-of-thought, template systems, system prompt design, agent prompting best practices, persuasion principles cho LLM interaction |
| `prompt-generator` | Meta-prompting, tạo prompt chất lượng cao |
| `prompt-generator-v2` | KERNEL framework, prompt engineering nâng cao |
| `sequential-thinking` | Phân tích từng bước cho vấn đề phức tạp, revision, branching, hypothesis verification |
| `skill-auto-improver` | Phân tích và cải tiến skill tự động, quality audit + improvement patterns |
| `social-post` | Viết bài social đa platform (Facebook, Threads, LinkedIn, Zalo) chia sẻ góc nhìn chiều sâu, anti-AI rules, self-critique |
| `style-writer` | Skill viết lách hợp nhất, 2 workflow: Writer (mặc định, viết nội dung theo voice + structure) + Analyze (bóc tách DNA văn phong → tạo voice mới). Gồm 7 voices generic + 8 structures |
| `substack-tools` | Quản lý bài viết Substack: draft, schedule, publish, list, sections + scan/crawl newsletter khác |
| `systems-thinking` | Phân tích tư duy hệ thống theo framework Donella Meadows, feedback loops, system traps, leverage points |
| `things-manager` | Quản lý Things 3 tasks, projects, areas, tags qua things-cli (Go CLI) |
| `trello` | Quản lý Trello workspaces, boards, lists, cards, labels, checklists, members, comments qua natural language (Trello REST API) |
| `wisdom-mentor` | Trò chuyện với người thầy tri thức (28 mentors) |
| `work-explainer` | Personal teacher, giải thích công việc đã làm qua 9-step framework |
| `workshop-builder` | Thiết kế workshop theo Backwards Design + 4Cs + Kirkpatrick |
| `speech-to-text` | Chuyển file audio/video thành text kèm timestamps qua Soniox API, hỗ trợ 60+ ngôn ngữ, audio (mp3/wav/flac) + video (mp4/mov/mkv/avi) |
| `youtube-title-generator` | Tạo tiêu đề YouTube hấp dẫn từ ý tưởng nội dung |
| `youtube-transcript` | Tải transcript (phụ đề/captions) từ YouTube video qua yt-dlp, convert VTT sang plain text |

### Agents

_Coming soon_ — Các agent chuyên biệt cho các workflow phức tạp.

### Hooks

_Coming soon_ — Các hook scripts chạy tự động theo sự kiện của Claude Code.

### MCP Servers

_Coming soon_ — Các MCP server cung cấp tool integration cho Claude Code.

## Development

Khi tạo skill mới, luôn sử dụng `/skill-creator` để bắt đầu:

```
/skill-creator
```

Skill creator sẽ hướng dẫn cấu trúc chuẩn và tạo các file cần thiết.

## License

MIT
