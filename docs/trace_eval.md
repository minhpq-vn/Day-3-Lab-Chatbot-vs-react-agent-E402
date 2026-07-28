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
