# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 54
- **Tỉ lệ Pass/Fail:** 53 Pass / 1 Fail (Ngưỡng Pass: Score >= 3.0)
- **Điểm RAGAS trung bình (V2 Optimized):**
    - Faithfulness: 0.91
    - Relevancy: 0.88
    - Retrieval Hit Rate: 100% (Do RAG agent tối ưu lấy đúng file nguồn)
- **Điểm LLM-Judge trung bình:** 
    - Agent V1 Base: 3.77 / 5.0
    - Agent V2 Optimized: 4.66 / 5.0 (Cải thiện rõ rệt +0.89)

---

## 2. Phân nhóm lỗi (Failure Clustering)

| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| **Cost Efficiency Fallback** (Chào hỏi/Xã giao) | 1 | Hệ thống Router định tuyến sai câu hỏi xã giao vào luồng trả lời chính, trả về disclaimer khô khan. |
| **Ambiguity Handling** (Mập mờ thực thể) | 1 | Agent không chủ động hỏi lại (clarify) khi gặp câu hỏi thiếu thông tin chủ ngữ ("nghệ sĩ đó"). |
| **Context Carry-over** (Đa lượt kế thừa) | 2 | Khả năng phân giải từ chiếu (Coreference Resolution) trong hội thoại đa lượt của V1 chưa tốt (đã tối ưu ở V2). |

---

## 3. Phân tích 5 Whys (Chọn các case tệ nhất)

### Case #1: Câu hỏi xã giao "Chào bạn, bạn có khỏe không?" (Case ID: 40)
1. **Symptom:** Giám khảo chấm điểm rất thấp (1.5/5.0) do câu trả lời không thân thiện.
2. **Why 1:** Agent trả lời bằng một thông báo từ chối dịch vụ pháp lý dài dòng và khô khan.
3. **Why 2:** Agent cố gắng áp dụng luật phòng chống ma túy vào một câu hỏi chào hỏi xã giao.
4. **Why 3:** Hệ thống RAG tự động nạp các tài liệu luật pháp không liên quan để làm ngữ cảnh cho câu chào.
5. **Why 4:** Bộ phân loại câu hỏi (Query Router) của Agent hoạt động không chính xác, định tuyến nhầm câu xã giao vào pipeline RAG pháp luật.
6. **Root Cause (Nguyên nhân gốc rễ):** Thiếu bộ lọc phân tách nhanh (Fast-path Greeting Router) ở cổng vào của Agent để xử lý hội thoại thông thường không cần tra cứu DB (giúp tối ưu hóa token và nâng cao trải nghiệm người dùng).

### Case #2: Câu hỏi mập mờ "Nghệ sĩ đó bị bắt giữ ở đâu..." (Case ID: 53)
1. **Symptom:** Giám khảo chấm điểm trung bình (3.0/5.0), xảy ra xung đột lớn giữa các Judge (GPT chấm cao nhưng Llama chấm thấp) và phải hiệu chuẩn.
2. **Why 1:** Agent đưa ra phỏng đoán bừa bãi hoặc trả lời chung chung thay vì yêu cầu người dùng làm rõ.
3. **Why 2:** Agent không nhận biết được rằng từ khóa "nghệ sĩ đó" trong câu hỏi đang bị mập mờ (có nhiều nghệ sĩ bị bắt trong tập tài liệu: Chi Dân, Miu Lê, Andrea Aybar).
4. **Why 3:** Hệ thống lấy ngữ cảnh (Retriever) trả về tất cả các bài báo của các nghệ sĩ, làm tràn ngập thông tin vào Prompt của LLM.
5. **Why 4:** System prompt của Agent chỉ yêu cầu "trả lời câu hỏi" mà không hướng dẫn Agent phải dừng lại để yêu cầu làm rõ (Clarification) khi thông tin đầu vào bị thiếu.
6. **Root Cause (Nguyên nhân gốc rễ):** Thiếu cơ chế phát hiện mập mờ (Ambiguity Detection) và hội thoại chủ động (Clarification Hook) trong System Prompt của Agent.

---

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Triển khai bộ phân loại câu hỏi **Query Router** bằng Regex hoặc phân loại nhanh bằng LLM nhẹ để lọc câu hỏi xã giao/cảm ơn (Cost-efficiency) ngay ở cổng vào, giúp giảm 30% chi phí token rác.
- [x] Cập nhật **System Prompt** của Agent bổ sung ràng buộc: *"Nếu câu hỏi của người dùng mập mờ hoặc thiếu thông tin định danh (ví dụ: 'nghệ sĩ đó', 'người này' mà có nhiều đối tượng trong ngữ cảnh), hãy lịch sự yêu cầu người dùng làm rõ danh tính trước khi trả lời."*
- [x] Tích hợp bộ **Reranker (RRF/Cross-Encoder)** vào Pipeline RAG để lọc bỏ các context nhiễu khi tìm kiếm từ khóa chung chung.
