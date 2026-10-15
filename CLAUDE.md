# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dự án phát triển các plugin cho Claude Code, bao gồm: **skills**, **agents**, **hooks**, và **MCP servers**. Mỗi plugin mở rộng khả năng của Claude Code cho các workflow chuyên biệt.

## Structure

```
.claude-plugin/plugin.json   # Plugin manifest
skills/                      # Các skill plugins (chi tiết xem ## Skill Structure)
  ai-artist/                 # Tạo ảnh qua Nano Banana — 129 curated prompts, validation interview, 3 modes
  anti-ai-writing/           # Rules viết tiếng Việt không giống AI — blacklist từ/cụm/chấm câu, self-critique, insight techniques (baseline cho mọi skill viết)
  codex-image/               # Tạo và chỉnh sửa ảnh 2 chế độ: Codex CLI (gpt-image-2, mặc định) + fallback OpenAI API — text-to-image, transparent (chroma-key + native gpt-image-1.5), batch, edit (style transfer + mask/high-fidelity)
  creative-thought-partner/  # Đối tác tư duy sáng tạo — brainstorming
  decision-gate/             # Trợ lý phán quyết go/no-go + ưu tiên cho MỘT hạng mục kỹ thuật mơ hồ (bug/feature/techdebt/task) — xác minh bằng chứng read-only trước, chấm điểm theo loại (RICE/ICE/WSJF), dừng ở decision brief
  deep-insight/              # Quan sát đa chiều → Phân tích tách lớp → Đúc kết cốt lõi để hiểu sâu vấn đề
  deep-learner/              # Dẫn dắt từng bước hiểu sâu bản chất nội dung — 4 lớp hiểu + áp dụng đời sống
  deep-reader/               # Bộ 10 command phân tích đa chiều: summary, explain, insights, concept map, critique, article, video script, questions, checklist, gap analysis
  facebook/                  # Facebook automation via PinchTab (wall post, attach images, tag friends)
  game-theory-lens/          # Phân tích chủ đề qua lăng kính Lý thuyết Trò chơi (Game Theory)
  ghost-blog/                # Ghost CMS blog management
  kinh-dich-lens/            # Phân tích tình huống qua Kinh Dịch: 64 Quẻ, Âm Dương tiêu trưởng, Ngũ Hành cân bằng, Biến Thông (Nguyên-Hanh-Lợi-Trinh), Đạo Quân Tử tu dưỡng
  m365-shared/               # CLI for Microsoft 365: shared patterns — authentication, installation, output formatting, common flags
  m365-calendar/             # Outlook calendar qua m365 CLI + Graph: đọc lịch theo khoảng (calendarView), CRUD calendar, tạo/sửa event, mời người, họp Teams, đặt phòng (beta findRooms), rảnh/bận (getSchedule), tìm giờ chung (findMeetingTimes), dời một buổi trong chuỗi lặp, huỷ/xoá
  m365-meeting/              # Transcript họp Teams qua Graph + SharePoint: tìm đúng buổi (họp định kỳ trùng tên, họp mình chỉ tham dự, họp kênh, link meetingrecap), kiểm tra languageTag/chất lượng, tải transcript ra .txt có header + .vtt gốc, fallback Soniox (hỏi trước), recording, điểm danh, preflight chẩn đoán 403
  m365-teams/                # Microsoft Teams management — teams, channels, messages, chats, members qua m365 CLI
  m365-onedrive/             # OneDrive personal file management — files, folders, sharing, versions qua m365 CLI (resolve URL non-admin qua Graph me/drive)
  m365-sharepoint/           # SharePoint Online — truy cập/ghi tài liệu nhóm (non-admin, resolve site qua group) + lists, list items, files, folders, permissions qua m365 CLI
  meeting-minutes/           # 2 workflow: (1) Tạo biên bản họp, (2) Phân tích hành vi giao tiếp (insights) — conflict avoidance, speaking ratio, filler words, active listening, facilitation
  n8n-cli/                   # Quản lý n8n instance qua n8n-cli (REST API) — workflows, executions, credentials, projects, tags, variables, data tables, users, audit
  nhat-di-quan-chi/          # Phân tích vấn đề thực tế bằng tư duy Đông phương tổng hợp (Thu Giang Nguyễn Duy Cần) — 4 giai đoạn: Tâm Thế, Phân Tích (Dịch Lý), Định Vị (Thời-Vị-Cơ), Hành Động (Vô Vi & Lưỡng Hành)
  outline-writer/            # Phân tích nội dung & tạo outline thuần nội dung (sequence of sections; thesis, key arguments, evidence) — không quyết định media (slide/blog/doc), không quy định cách viết/tone/style
  pexels-media/              # Source ảnh/video royalty-free từ Pexels API — search, curated, collections, multi-resolution download + sidecar metadata bắt buộc
  pinchtab/                  # Browser automation for AI agents via PinchTab HTTP API
  planning-content/          # Phân tích nội dung & lên outline ý chính cho từng bài. Hỗ trợ mọi input: topic, notes, URL, file (PDF/DOCX/EPUB/XLSX/PPTX), YouTube. Convert tài liệu, research, content map, tier processing cho tài liệu lớn
  problem-solving/           # Kỹ thuật giải quyết vấn đề có hệ thống — inversion, collision-zone, scale-game
  project-memory/            # Bộ nhớ tri thức cấp dự án tự cải tiến — 3 op (capture/consolidate/recall), 3 loại entry (Tool/Map/Fact), index routing, script Python giữ index đồng bộ
  pptx-creator/              # Tạo PowerPoint đẹp, chuyên nghiệp — hỗ trợ font tiếng Việt (PptxGenJS)
  prompt-engineering/        # Prompt engineering patterns, agent prompting best practices, persuasion principles cho LLM interaction
  prompt-generator/          # Meta-prompting — tạo prompt chất lượng cao
  prompt-generator-v2/       # KERNEL framework — prompt engineering nâng cao
  sequential-thinking/       # Phân tích từng bước cho vấn đề phức tạp — revision, branching, hypothesis
  skill-auto-improver/       # Phân tích và cải tiến skill tự động — quality audit + improvement patterns
  social-post/               # Viết bài social đa platform (Facebook, Threads, LinkedIn, Zalo) chia sẻ góc nhìn chiều sâu — anti-AI rules, self-critique
  speech-to-text/            # Chuyển file audio/video thành text kèm timestamps qua Soniox API — hỗ trợ 60+ ngôn ngữ, audio (mp3/wav/flac) + video (mp4/mov/mkv/avi)
  style-writer/              # Skill viết lách hợp nhất — 2 workflow: Writer (mặc định, viết nội dung theo voice + structure) + Analyze (bóc tách DNA văn phong → tạo voice mới). Gồm voices (5 generic + 3 analyzed) + structures (8 loại)
  substack-tools/            # Quản lý bài viết Substack: draft, schedule, publish, list, sections + scan/crawl newsletter khác
  systems-thinking/          # Phân tích tư duy hệ thống theo framework Donella Meadows (Thinking in Systems)
  things-manager/            # Things 3 task management via things-cli (Go CLI)
  trello/                    # Quản lý Trello workspaces, boards, lists, cards, labels, checklists, members qua natural language (Trello REST API)
  tri-thuc-goc/              # Giải quyết vấn đề qua lăng kính Tri Thức Gốc (Sự Thật Man) — 2 mode: phân tích (mặc định) + đối thoại nhập vai. 3 công thức: Sống Hiệu Quả, Xử Lý Tò Mò, 4T Xử Lý Vấn Đề
  wisdom-mentor/             # Trò chuyện với người thầy tri thức (28 mentors)
  work-explainer/            # Personal teacher — giải thích công việc đã làm (9-step framework)
  workshop-builder/          # Thiết kế workshop theo Backwards Design + 4Cs + Kirkpatrick
  youtube-title-generator/   # Tạo tiêu đề YouTube hấp dẫn
  youtube-transcript/        # Tải transcript (phụ đề/captions) từ YouTube video qua yt-dlp, convert VTT sang plain text
agents/                      # Các agent definitions (planned)
hooks/                       # Các hook scripts (planned)
mcp/                         # Các MCP server configs (planned)
```

## Skill Structure

Mỗi skill là một thư mục trong `skills/`. Cấu trúc chuẩn:

```
skills/<skill-name>/
  SKILL.md                   # [BẮT BUỘC] Prompt chính — load khi skill được gọi
  references/                # [Tùy chọn] Tài liệu tham khảo, rules, examples
  scripts/                   # [Tùy chọn] Shell/Python scripts thực thi
  templates/                 # [Tùy chọn] Templates cho output
```

**Quy tắc path quan trọng cho AI:**

- **Entry point**: Luôn là `skills/<skill-name>/SKILL.md` — đây là file duy nhất được load tự động khi skill được gọi.
- **References**: Nằm trong `skills/<skill-name>/references/` — SKILL.md reference đến các file này, AI load khi cần tra cứu.
- **Scripts**: Nằm trong `skills/<skill-name>/scripts/` — các script thực thi (shell, python). Chạy từ thư mục gốc project.
- **Templates**: Nằm trong `skills/<skill-name>/templates/` — template cho output format.
- **KHÔNG** dùng `docs/` làm subdirectory trong skill (dùng `references/` thay thế).

### Chi tiết từng skill

| Skill                      | Subdirectories                                                       | Ghi chú                                                                                                                                                                                                                              |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ai-artist`                | `references/` `scripts/` `data/`                                     | nano-banana, image-prompting, validation-workflow, domain guides, awesome-prompts.csv, styles/techniques/lighting CSVs                                                                                                               |
| `anti-ai-writing`          | —                                                                    | Chỉ có SKILL.md (rule chung viết tiếng Việt không giống AI)                                                                                                                                                                          |
| `codex-image`              | `scripts/` `references/`                                             | 2 chế độ: `codex exec` (mặc định, ChatGPT login) + fallback `image_gen.py` gọi thẳng OpenAI API (cần OPENAI_API_KEY). Scripts vendor từ OpenAI (Apache 2.0): image_gen.py (generate/edit/generate-batch), remove_chroma_key.py (auto-key, soft matte, despill); batch-generate.py cho đường codex exec. References: prompting, sample-prompts, cli, image-api, size-guide |
| `creative-thought-partner` | —                                                                    | Chỉ có SKILL.md                                                                                                                                                                                                                      |
| `decision-gate`            | `references/` `templates/`                                           | frameworks (RICE/ICE/WSJF, map khung↔loại, map điểm→P-level định tính), verification-tactics (đào bằng chứng read-only theo loại), decision-brief template. Luồng 3 pha: Xác minh (read-only, hỏi nhiều lần) → Cổng Go/No-Go (checkpoint 1 lần, gán loại, verdict) → Ưu tiên (chỉ khi Go). Dừng tuyệt đối ở brief |
| `deep-insight`             | `references/`                                                        | framework-foundation, observation-guide, analysis-patterns, synthesis-methods                                                                                                                                                        |
| `deep-learner`             | `references/` `templates/`                                           | easy-explain-guide, long-content-strategy, note-structure, output-template                                                                                                                                                           |
| `deep-reader`              | —                                                                    | Chỉ có SKILL.md. 10 command phân tích đa chiều: summary, explain, insights, map, critique, article, script, questions, checklist, gaps                                                                                               |
| `facebook`                 | `scripts/` `references/`                                             | fb-post.sh, snap-helpers.py, tag-search.py. Hỗ trợ text + ảnh (multi-image) + tag friends                                                                                                                                           |
| `game-theory-lens`         | `references/` `templates/`                                           | core-concepts, strategic-games, information-signaling, repeated-games-trust, mechanism-design, evolution-cooperation, bargaining-coalitions, paradoxes-fallacies, analysis-output                                                    |
| `ghost-blog`               | `scripts/`                                                           | Python scripts + tests cho Ghost CMS API                                                                                                                                                                                             |
| `kinh-dich-lens`           | `references/` `templates/`                                           | que-dich, am-duong-tieu-truong, ngu-hanh, bien-thong, quan-tu-dao, dich-hoc-tinh-hoa, analysis-output. 5 bước: Nhận diện Quẻ & Lục Hào → Âm Dương (Nhất Nguyên Lưỡng Cực Động, Tích Tiệm, Tham Thiên Lưỡng Địa) → Ngũ Hành cân bằng → Chu kỳ & Biến Thông (Tứ Tượng thực, Nội/Ngoại Thời) → Đúc kết & Đạo Quân Tử (Tẩy Tâm, Vô Vọng, Trường Xuân Bất Lão) |
| `m365-shared`              | `references/`                                                        | CLI for Microsoft 365 shared patterns: authentication (5 methods), installation check, output formatting (json + JMESPath), error handling, security rules |
| `m365-calendar`            | `references/` `scripts/`                                             | Outlook calendar via m365 CLI + Graph (`m365 request`). Native: `outlook calendar` CRUD, `event get/list/cancel/remove`. Graph: `calendarView` (đường đọc mặc định vì `event list` không bung event lặp lại, 12 so với 46 event cùng một tuần), POST/PATCH event, `getSchedule`, `findMeetingTimes`, `beta/me/findRooms` (v1.0 `/places` 403). Bảng 8 bẫy đã đo thật: thiếu header `Prefer` lệch 7 tiếng, `--userName` bắt buộc (trừ cancel/remove), ID `occurrence` vs `seriesMasterId`, `range.startDate` dịch ngày âm thầm. `scripts/date-range.sh` neo khoảng thời gian vào nửa đêm GMT+7 |
| `m365-meeting`             | `references/` `scripts/` `tests/`                                    | Transcript Teams qua Graph + SharePoint. 3 đường theo thứ tự: **bulk** `getAllTranscripts(meetingOrganizerUserId=...)` cho họp mình tổ chức, **per-thread** dựng `meetingId` = base64(`1*{oid}*0**{threadId}`) từ join URL cho họp mình tham dự (đã đo chạy thật trên họp thường), rồi **SharePoint** `<site>/_api/v2.1/drives/{d}/items/{i}/media/transcripts` cho họp kênh `thread.tacv2` hoặc link `meetingrecap` (Graph cùng path trả 400, `streamContent` 406, `temporaryDownloadUrl` có hạn; mới đo 1 lần). Scripts: `preflight.sh` (4 trạng thái chính sách tenant + scope trong token + câu nhắn IT), `list-transcripts.sh` (phân trang: trang 1 chỉ 6/9 item, `nextLink` sống sót cả khi trang rỗng), `meeting-resolver.py` (ghép transcript với lịch theo instant, chọn đúng buổi trong chuỗi lặp; subcommand `match`/`attended [--include-channel]`/`meeting-id`/`decode`), `sharepoint-transcript.py` (`parse` link recap → driveId/driveItemId/siteUrl, `find` mp4 theo tên file, `list` kèm cảnh báo languageTag ≠ vi-VN, `download` tải tempauth ngay trong cùng lần chạy), `transcript-quality.py` (tỷ lệ từ có chữ tiếng Việt + từ/phút, exit 2 khi kém → đề xuất `soniox --language-hints vi,en`, phải hỏi user trước khi gửi audio ra ngoài), `transcript-to-text.py` (VTT hoặc `metadataContent` → `.txt`, gộp cue cùng người <3s, cắt lượt >60s, giữ `@n`). Bẫy chính: `startDateTime`/`endDateTime` và `$filter` đều bị bỏ qua âm thầm. Tests offline trong `tests/` (68 test, `run-tests.sh`). Dừng ở tải file, không tóm tắt |
| `m365-teams`               | `references/`                                                        | Microsoft Teams via m365 CLI. 5 nhóm chính: Team CRUD (list/get/add), Channel (list/get/add/remove), Message (list/send/get), Chat (list/send 1:1 & group), Member (team users/channel members add/remove). Advanced: Tab, Meeting, App, Settings |
| `m365-onedrive`            | —                                                                    | OneDrive personal files via m365 CLI (spo commands + OneDrive URL). 5 nhóm: Discover (resolve URL + storage **non-admin** qua Graph `me/drive`), File (list/upload/download/copy/move/delete), Folder (list/add/copy/move/remove — remove dùng `--url`), Share (sharing links CRUD), Version (list/get/restore — dùng `--label`) |
| `m365-sharepoint`          | `references/`                                                        | SharePoint Online via m365 CLI — trọng tâm: truy cập/ghi **tài liệu nhóm/Teams** (resolve site qua group, non-admin). 6 nhóm: Site (resolve group site non-admin; `site list/get/add` cần admin), List (list/get/add), ListItem (list/get/add/set/remove + CAML), File (list/upload/download/copy/move + checkin/checkout — dùng `--url`), Folder (list/add/copy/move/remove — remove dùng `--url`), Permission (users/groups/sharing links). Advanced: Page, Search, Content Type, Hub Site, Site Design, Tenant |
| `meeting-minutes`          | `references/`                                                        | minutes-schema, insights-patterns. 2 workflow: Minutes (biên bản) + Insights (phân tích giao tiếp). Dừng khi transcript kém (sai ngôn ngữ/mất nội dung). Speaker ẩn danh → "Chưa xác định owner"                                                                                                                                   |
| `n8n-cli`                  | —                                                                    | Chỉ có SKILL.md. CLI quản lý n8n instance qua REST API: workflow (CRUD/activate/transfer), execution (list/retry/stop), credential (schema trước khi create), project/tag/variable/data-table/user, audit, source-control. Auto-JSON khi pipe, `--jq` filter, cấu hình qua login/config/env vars |
| `nhat-di-quan-chi`         | `references/`                                                        | thuat-tu-tuong, dich-ly, vo-vi-luong-hanh. 4 giai đoạn: Tẩy Tâm (loại thiên kiến) → Mổ Xẻ (Dịch Lý: Lưỡng Nghi, Tứ Tượng, Tiêu Trưởng) → Định Vị (Thời-Vị-Cơ, Phản Phục) → Hành Động (Hoàn Trung, Lưỡng Hành, Vô Vi)           |
| `outline-writer`           | `references/`                                                        | content-map-rules, detail-levels, framework-mapping, outline-structure, report-format. Outline thuần nội dung (sequence of sections), không quyết định media, không quy định cách viết/tone/style                                     |
| `pexels-media`             | —                                                                    | Chỉ có SKILL.md. Source ảnh/video royalty-free từ Pexels API (search, curated, popular, collections). Download multi-resolution + sidecar metadata (.meta.json) bắt buộc cho mỗi file                                                |
| `pinchtab`                 | `references/`                                                        | api-reference, cli-reference, workflow-patterns                                                                                                                                                                                      |
| `planning-content`         | `references/` `scripts/`                                             | Phân tích input → convert (PDF/DOCX/EPUB/URL/YouTube) → research → outline ý chính. Tier processing cho tài liệu lớn (Standard/<50K, Tier 2/50-100K, Tier 3/>=100K). Batch + content map + coverage check. Luôn bao phủ 100% nội dung nguồn. KHÔNG can thiệp cách viết/tone/style |
| `problem-solving`          | `references/`                                                        | collision-zone-thinking, inversion-exercise, meta-pattern-recognition, scale-game, simplification-cascades, when-stuck                                                                                                               |
| `project-memory`           | `references/` `scripts/`                                             | schemas, consolidation (lint + cross-ref 2 chiều), capture-signals, self-contained-exec. Scripts Python stdlib: _common, new-entry, reindex, archive. Dữ liệu ghi memory/ ở gốc repo. recall gộp tra cứu + thực thi, consolidate tách riêng không tự nhảy sang recall |
| `pptx-creator`             | `references/` `scripts/`                                             | design-system, slide-types, pptxgenjs-api, compile.js                                                                                                                                                                                |
| `prompt-engineering`       | —                                                                    | Chỉ có SKILL.md. Few-shot, chain-of-thought, template systems, system prompt design, agent prompting, persuasion principles                                                                                                         |
| `prompt-generator`         | —                                                                    | Chỉ có SKILL.md                                                                                                                                                                                                                      |
| `prompt-generator-v2`      | —                                                                    | Chỉ có SKILL.md                                                                                                                                                                                                                      |
| `sequential-thinking`      | `references/` `scripts/` `tests/`                                    | core-patterns, examples (api/debug/architecture), advanced-techniques, advanced-strategies, process-thought.js, format-thought.js                                                                                                    |
| `skill-auto-improver`      | `references/`                                                        | quality-checklist, improvement-patterns                                                                                                                                                                                              |
| `social-post`              | `references/`                                                        | archetypes, craft-techniques, anti-ai-rules (social-post specific, references anti-ai-writing cho baseline), example-output                                                                                                          |
| `speech-to-text`           | `references/` `scripts/`                                             | Soniox async API, transcribe.js (Node.js), audio + video (ffmpeg extract), output timestamps/text/SRT, 60+ ngôn ngữ                                                                                                                 |
| `style-writer`             | `references/voices/` `references/structures/`                        | voices (5 generic + 3 analyzed), structures (8 loại), analysis-dimensions, anti-patterns, output-template, shared-rules, value-framework. Workflow Writer (mặc định, 2 tầng ngắn/dài) + Analyze (output → voices/)                   |
| `substack-tools`           | `references/` `scripts/`                                             | substack_cli.py, substack_crawl.py, api-quirks, batch-operations, crawl-guide                                                                                                                                                        |
| `systems-thinking`         | `references/` `templates/`                                           | system-traps, leverage-points, systems-wisdom, analysis-output                                                                                                                                                                       |
| `things-manager`           | —                                                                    | Chỉ có SKILL.md                                                                                                                                                                                                                      |
| `trello`                   | `references/`                                                        | Natural language → Trello REST API. Workspaces (CRUD, list boards/members), Boards (CRUD), Lists (CRUD, archive, moveAllCards), Cards (CRUD, move, archive, due date), Labels (CRUD, assign), Checklists (CRUD, check items), Members (assign/unassign), Comments, Search. Auth: TRELLO_API_KEY + TRELLO_TOKEN env vars |
| `tri-thuc-goc`             | `references/`                                                        | core-philosophy, formulas, three-games, su-that-man-persona. 2 mode: Phân tích (áp dụng framework) + Đối thoại (nhập vai Sự Thật Man). 3 công thức gốc: Sống Hiệu Quả, Xử Lý Tò Mò (5 tủ tri thức), 4T Xử Lý Vấn Đề             |
| `wisdom-mentor`            | `references/`                                                        | 28 mentor profiles (mỗi mentor 1 file .md)                                                                                                                                                                                           |
| `work-explainer`           | —                                                                    | Chỉ có SKILL.md                                                                                                                                                                                                                      |
| `workshop-builder`         | `references/`                                                        | frameworks, activity-library, templates, example-walkthrough, prepare-deliver-followup                                                                                                                                               |
| `youtube-title-generator`  | `references/`                                                        | title-examples                                                                                                                                                                                                                       |
| `youtube-transcript`       | `references/` `scripts/`                                             | Tải transcript YouTube qua yt-dlp. vtt-to-txt.py (convert/dedup), whisper-guide, error-handling                                                                                                                                      |


## Installation

```bash
claude plugin install gh:hoangvantuan/skills
```

## Development Workflow

### Tạo skill mới

Luôn sử dụng `/skill-creator` để bắt đầu tạo skill mới. Skill creator sẽ hướng dẫn cấu trúc chuẩn và tạo các file cần thiết (SKILL.md, prompt, scripts).

### Development Principles

- **YAGNI/KISS/DRY** - Minimal, focused implementations
- **kebab-case** file naming with descriptive names
- **<200 lines** per code file
- Mỗi skill/agent/hook/mcp là một thư mục độc lập trong folder tương ứng

### Auto-update Documentation

Khi thêm, xóa, hoặc đổi tên bất kỳ tính năng nào (skill, agent, mcp, hook), **tự động cập nhật** lại:

- **CLAUDE.md** — cập nhật phần `## Structure` cho đúng cấu trúc hiện tại
- **README.md** — cập nhật danh sách tính năng và mô tả tương ứng

### Single Source of Truth

- Mỗi thông tin chỉ được định nghĩa **một nơi duy nhất**. Không copy nội dung giữa các file — thay vào đó reference đến file gốc.
- CLAUDE.md chỉ chứa rules tổng quan của dự án. Hướng dẫn chi tiết cho từng skill/agent/hook/mcp nằm trong SKILL.md hoặc README riêng của thư mục đó.
- Khi cần hướng dẫn phân nhánh (chi tiết, ví dụ cụ thể, API specs), **tách thành file riêng** và reference bằng đường dẫn. Claude Code sẽ load file khi cần thay vì load hết vào context.

Ví dụ cấu trúc reference:

```
skills/ghost-blog/
  SKILL.md                    # Prompt chính — load khi skill được gọi
  references/api-reference.md # Chi tiết API — load khi cần tra cứu
  references/examples.md      # Ví dụ — load khi cần tham khảo
```
