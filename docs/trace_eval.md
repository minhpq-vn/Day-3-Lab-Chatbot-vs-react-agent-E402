# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Phải suy luận qua nhiều bước: tra cứu đơn hàng → kiểm tra tình trạng giao hàng → đối chiếu chính sách đổi trả (thời hạn, điều kiện) → ra quyết định chấp nhận/từ chối. |
| 🛠️ **Tool Interaction** | `5/5` | Cần gọi tool tra cứu đơn hàng theo mã đơn (database/API), tool kiểm tra chính sách đổi trả, và có thể tool tính số ngày kể từ khi nhận hàng. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả tra cứu (VD: đơn đã giao 20 ngày trước) quyết định hoàn toàn hành động tiếp theo (được đổi/không được đổi/cần hỏi thêm lý do). |
| ⏳ **Long Horizon** | `3/5` | Quy trình thường gồm 2-4 bước xử lý, không quá dài nhưng có rẽ nhánh logic. |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT — Chatbot thuần không thể tra cứu dữ liệu đơn hàng thực tế hay áp dụng chính sách theo từng trường hợp cụ thể.** |


---
## 2. Ghi nhận phản hồi Chatbot Baseline (Mốc 2)

> LLM Provider: GeminiProvider (gemini-3.5-flash). Chạy 5/5 test cases từ `config/test_cases.json`.

| # | Câu hỏi test | Chatbot trả lời được gì? | Vấn đề quan sát được |
|---|---|---|---|
| TC1 🟢 Đơn giản | "Cần cung cấp thông tin gì để tra cứu & đổi trả?" | Trả lời tốt — đây là câu hỏi *tĩnh* (quy trình chung), không cần dữ liệu thật. | Không có vấn đề — đúng dạng câu Chatbot xử lý tốt. |
| TC2 🟡 Cần 1 Tool | "Trạng thái đơn ORD-1003?" | Từ chối trả lời, tự nhận "không có quyền truy cập hệ thống thời gian thực", đẩy khách sang hotline. | **Không hallucinate** (điểm cộng an toàn) nhưng **không hoàn thành được tác vụ** — đây chính là giới hạn cốt lõi của Chatbot Cấp 2. |
| TC3 🟡 Cần 2 Tools | "ORD-1001 thuộc danh mục nào, chính sách đổi trả ra sao?" | Từ chối tra đơn hàng cụ thể, nhưng bù lại bằng chính sách đổi trả *chung chung* theo từng danh mục (Thời trang 7 ngày, Điện tử 3–7 ngày, Mỹ phẩm...). | Nguy hiểm tiềm ẩn: các con số chính sách (7 ngày, 3-7 ngày...) là **do LLM tự sinh**, không chắc khớp với chính sách thật của cửa hàng → rủi ro hallucination "ẩn" dưới dạng thông tin nghe hợp lý. |
| TC4 🟡 Multi-step | "Đổi ORD-1001 vì áo không vừa size — kiểm tra & gửi yêu cầu giúp tôi" | Không kiểm tra, không tạo yêu cầu đổi trả. Chỉ đưa ra chính sách chung + hướng dẫn liên hệ hotline. | Bằng chứng rõ nhất cho **Agentic Fit tiêu chí 2 & 3**: tác vụ cần hành động thật (tạo yêu cầu) và suy luận nhiều bước (tra đơn ➔ check điều kiện ➔ tạo yêu cầu) — Chatbot hoàn toàn bó tay ở bước đầu tiên. |
| TC5 🔴 Edge case | "Trả ORD-1002 vì tai nghe không còn phù hợp nhu cầu" | Tương tự TC4: không tra cứu, chỉ đưa chính sách chung rồi đẩy sang người thật. | Vì Chatbot không tra cứu được nên **cũng không có rủi ro duyệt sai** — nhưng đó là vì nó "bó tay" toàn bộ chứ không phải vì nó thông minh. Chính là lý do cần ReAct Agent: vừa tra cứu được thật, vừa phải có Guardrail để không duyệt sai. |

### 🔑 Kết luận rút ra cho Role 5 (đưa vào báo cáo Agentic Fit)
1. **Điểm mạnh của Chatbot baseline**: không bịa trạng thái đơn hàng cụ thể (không nói khống "đơn đã giao ngày X") — nó thành thật về giới hạn của mình.
2. **Điểm yếu chí mạng**: 100% test case cần dữ liệu thật (TC2–TC5) đều bị đẩy sang con người → Chatbot **không tự động hoá được gì**, chỉ đóng vai trò FAQ tĩnh.
3. **Rủi ro ẩn cần nêu bật**: ở TC3, Chatbot vẫn "sáng tác" ra các con số chính sách (7 ngày, 3-7 ngày…) nghe rất thật nhưng không có nguồn xác thực — đây là dạng hallucination nguy hiểm hơn vì khó phát hiện.
4. **➔ Luận điểm cho Mốc 3**: ReAct Agent cần tool `check_return_eligibility()` để thay thế hoàn toàn các con số bịa này bằng dữ liệu tra cứu thật, và cần Guardrail để không tự ý duyệt đổi trả chỉ vì người dùng yêu cầu.

---

## 3. Trace Log — ReAct Agent (Mốc 3)

> LLM Provider: GeminiProvider (gemini-3.5-flash). MAX_ITERATIONS = 3. Chạy 5/5 test cases.

### ✅ TC1 🟢 (1 bước) — Câu hỏi tĩnh, không cần Tool
```
[Thought] Đã đủ thông tin để trả lời dựa trên quy tắc chung (không cần tra dữ liệu thật).
[Final Answer] Cần Mã đơn hàng + Lý do đổi trả để tiến hành kiểm tra và tạo yêu cầu.
```
Đúng như kỳ vọng — Agent nhận ra không cần gọi Tool cho câu hỏi loại FAQ.

### ✅ TC2 🟡 (2 bước) — Tra cứu 1 Tool
```
[Thought] Cần tra cứu trạng thái đơn ORD-1003.
[Action] get_order_status[ORD-1003]
[Observation] Sản phẩm: Giày chạy bộ Bitis (Fashion) | 850,000đ | Trạng thái: Shipping
[Thought] Đã có dữ liệu thật, trả lời.
[Final Answer] Đơn ORD-1003 hiện đang "Đang giao hàng".
```
So với Chatbot Baseline (từ chối trả lời) — đây là bằng chứng trực quan nhất cho việc Agent tạo giá trị thật.

### ⚠️ TC3 🟡 (2 Tools kỳ vọng) — **LỖI: Agent không hoàn thành**
```
[Thought] Cần tra ORD-1001 để biết danh mục sản phẩm.
[Action] get_order_status[ORD-1001]
[Observation] Sản phẩm: Áo thun nam basic (Fashion) | 250,000đ | Delivered 2026-07-27

--- Step 2/3 ---
(không có Thought/Action/Final Answer nào được sinh ra — log trống)
```
**🐞 Bug ghi nhận cho Role 2 & 3 xử lý:**
- Agent đã lấy được danh mục "Fashion" ở bước 1 nhưng **không gọi tiếp Tool tra chính sách đổi trả** (ví dụ `get_return_policy` hay tương đương) để hoàn tất câu hỏi 2 vế ("thuộc danh mục nào **và** chính sách đổi trả ra sao").
- Nghi vấn nguyên nhân: (a) Thiếu Tool tra cứu chính sách theo danh mục trong `tools.py`, khiến Agent không có Action nào để chọn ở bước 2; hoặc (b) Prompt không có Guardrail "nếu không có Action phù hợp, phải trả Final Answer để không bị treo vòng lặp" → Agent sinh ra output rỗng thay vì dừng.
- **Đây chính là ví dụ thật cho mục 3 "Guardrails & Observability"** trong rubric — nên đưa case này vào phần "Bắt được lỗi loop" thay vì giấu đi, vì phát hiện + giải thích được lỗi cũng được tính điểm.

### ✅ TC4 🟡 (3 bước, multi-step, đủ điều kiện) — Guardrail hoạt động đúng
```
[Action] get_order_status[ORD-1001] → Fashion, Delivered 2026-07-27
[Thought] Đã giao 1 ngày, danh mục Fashion (hạn 7 ngày) → đủ điều kiện.
[Action] request_return[ORD-1001, "áo mặc không vừa size"]
[Observation] DUYỆT THÀNH CÔNG — Fashion hạn 7 ngày, đã giao 1 ngày.
[Final Answer] Yêu cầu đổi trả ORD-1001 đã được duyệt. Giữ nguyên tem mác...
```
Agent tự kiểm tra điều kiện (7 ngày) trước khi duyệt — không duyệt mù theo yêu cầu của khách. Đúng tinh thần Guardrail.

### ✅ TC5 🔴 (Edge case — quá hạn) — Guardrail chặn thành công
```
[Action] get_order_status[ORD-1002] → Electronics, Delivered 2026-07-10
[Action] request_return[ORD-1002, "..."] 
[Observation] TỪ CHỐI — Electronics hạn 15 ngày, đã giao 18 ngày → quá hạn.
[Final Answer] Yêu cầu bị từ chối do quá hạn 15 ngày (đã 18 ngày).
```
Đây là bằng chứng Guardrail mạnh nhất: Agent **tự động từ chối** dựa trên logic ngày tháng thật (2026-07-10 → 2026-07-28 = 18 ngày > 15 ngày cho phép), không bị thao túng bởi lời lẽ thuyết phục của khách ("không còn phù hợp nhu cầu").

### 📌 Bảng so sánh nhanh Baseline vs ReAct (dùng cho slide)

| Test case | Chatbot Baseline | ReAct Agent |
|---|---|---|
| TC2 (tra cứu) | ❌ Từ chối, đẩy sang hotline | ✅ Trả lời đúng trạng thái thật |
| TC3 (2 tools) | ⚠️ Bịa chính sách chung chung | ⚠️ Lấy đúng danh mục nhưng bug ở bước 2 (chưa lấy được chính sách) |
| TC4 (duyệt đổi trả) | ❌ Không làm gì, đẩy sang người | ✅ Tự kiểm tra điều kiện rồi duyệt đúng |
| TC5 (từ chối đổi trả) | ❌ Không kiểm tra được | ✅ Tự tính số ngày và từ chối đúng chính sách |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có truy cập Internet thời gian thực nên không biết thời tiết hôm nay ở Hà Nội."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu thời tiết Hà Nội.
* **Action 1**: `get_weather['Hà Nội']`
* **Observation 1**: `Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%.`
* **Thought 2**: Đã có thông tin 28°C nắng nhẹ, đưa ra lời khuyên trang phục.
* **Final Answer**: *"Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc quần áo thoáng mát!"*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.
