# Kịch bản voiceover — Video demo Tool Autopost (chạy thật `run-batch`)

- **Thời lượng mục tiêu:** ~75 giây (linh hoạt 60–90s).
- **Tốc độ đọc gợi ý:** vừa phải, khoảng 2,5–3 từ/giây. Nghỉ ngắn giữa các cảnh.
- **Giọng đọc gợi ý:** nam hoặc nữ, tự tin, thân thiện, hơi nhanh ở đoạn kỹ thuật để bám kịp log chạy trên màn hình.
- **Lưu ý:** Không nhắc Facebook. Nhấn các điểm mạnh có thật: viết bài SEO bằng AI, ảnh gắn logo, internal link, SEO RankMath, ghi kết quả về Excel.

---

## Kịch bản chia cảnh

### Cảnh 1 — Hook (0:00–0:10)
**Trên màn hình:** Mở file `data/keywords.xlsx`, kéo qua các dòng có trạng thái `Pending` (cột từ khóa, search intent, đối tượng, chuyên mục).

**Lời đọc:**
> "Bạn có một danh sách từ khóa cần lên bài, nhưng viết tay thì mất cả ngày. Với công cụ này, mỗi từ khóa sẽ tự động thành một bài chuẩn SEO — có ảnh, có internal link, đăng thẳng lên WordPress."

---

### Cảnh 2 — Chạy lệnh (0:10–0:22)
**Trên màn hình:** Cửa sổ terminal, gõ `python main.py run-batch 3` rồi Enter. Log bắt đầu chạy: `DRY_RUN is OFF — hitting real services.` và `Batch 1/3 — processing next Pending keyword.`

**Lời đọc:**
> "Mình chỉ cần một lệnh duy nhất: run-batch ba. Công cụ sẽ xử lý ba bài liên tiếp, hoàn toàn tự động."

---

### Cảnh 3 — Pipeline chạy (0:22–0:40)
**Trên màn hình:** Log chạy lần lượt: `Processing row N — keyword: …`, `Found N internal link candidate(s).`, `Saved branded image output\img_xxx.webp`.

**Lời đọc:**
> "Với mỗi từ khóa, nó lấy dòng Pending đầu tiên, tìm các internal link phù hợp, rồi để AI viết nguyên một bài chuẩn SEO. Sau đó tự tạo ảnh minh họa gắn logo thương hiệu và chèn vào dưới các tiêu đề."

---

### Cảnh 4 — Đăng bài (0:40–0:52)
**Trên màn hình:** Log `Row N SUCCESS — web: https://…` xuất hiện lần lượt cho từng bài.

**Lời đọc:**
> "Bài viết được đăng thẳng lên WordPress, kèm tiêu đề SEO, thẻ mô tả và từ khóa chính cho RankMath. Cứ mỗi dòng SUCCESS là một bài đã lên sóng."

---

### Cảnh 5 — Kết quả (0:52–1:05)
**Trên màn hình:** Quay lại `keywords.xlsx` — các dòng giờ hiện `Success`, `Link Website`, thời gian đăng. Sau đó mở nhanh một bài trên WordPress (ảnh đại diện, ảnh trong bài, internal link).

**Lời đọc:**
> "Kết quả được ghi ngược lại file Excel: trạng thái Success, đường link bài viết và thời gian đăng. Mở lên là một bài hoàn chỉnh — có ảnh đại diện, ảnh trong bài và các liên kết nội bộ."

---

### Cảnh 6 — Chốt (1:05–1:15)
**Trên màn hình:** Log cuối: `Batch finished — processed 3 post(s) out of 3 requested.`

**Lời đọc:**
> "Ba bài chỉ trong một lần chạy. Muốn tự động hoàn toàn, chỉ cần hẹn giờ bằng Windows Task Scheduler. Đơn giản vậy thôi."

---

## Bản lời đọc liền mạch (copy vào TTS)

Bạn có một danh sách từ khóa cần lên bài, nhưng viết tay thì mất cả ngày. Với công cụ này, mỗi từ khóa sẽ tự động thành một bài chuẩn SEO — có ảnh, có internal link, đăng thẳng lên WordPress.

Mình chỉ cần một lệnh duy nhất: run-batch ba. Công cụ sẽ xử lý ba bài liên tiếp, hoàn toàn tự động.

Với mỗi từ khóa, nó lấy dòng Pending đầu tiên, tìm các internal link phù hợp, rồi để AI viết nguyên một bài chuẩn SEO. Sau đó tự tạo ảnh minh họa gắn logo thương hiệu và chèn vào dưới các tiêu đề.

Bài viết được đăng thẳng lên WordPress, kèm tiêu đề SEO, thẻ mô tả và từ khóa chính cho RankMath. Cứ mỗi dòng SUCCESS là một bài đã lên sóng.

Kết quả được ghi ngược lại file Excel: trạng thái Success, đường link bài viết và thời gian đăng. Mở lên là một bài hoàn chỉnh — có ảnh đại diện, ảnh trong bài và các liên kết nội bộ.

Ba bài chỉ trong một lần chạy. Muốn tự động hoàn toàn, chỉ cần hẹn giờ bằng Windows Task Scheduler. Đơn giản vậy thôi.
