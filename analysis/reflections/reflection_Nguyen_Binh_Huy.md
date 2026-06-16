# Báo cáo Thu hoạch Cá nhân (Individual Reflection Report)

**Sinh viên:** Nguyễn Binh Huy  
**Mã sinh viên:** 2A202600689  
**Vai trò:** AI Engineer / Data Engineer (Thực hiện Cá nhân)

---

## 1. Các Khái niệm Kỹ thuật Chuyên sâu (Technical Depth)

### 1.1. Mean Reciprocal Rank (MRR) là gì?
*   **Định nghĩa**: MRR là một chỉ số thống kê để đánh giá chất lượng của các hệ thống xếp hạng hoặc truy xuất thông tin (Retriever). Nó đo lường thứ hạng của tài liệu chính xác đầu tiên (Ground Truth) được tìm thấy trong danh sách kết quả trả về.
*   **Công thức**:
    $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
    Trong đó:
    *   $|Q|$ là tổng số câu hỏi truy vấn.
    *   $\text{rank}_i$ là vị trí của tài liệu đúng đầu tiên xuất hiện trong kết quả truy xuất của câu hỏi thứ $i$. Nếu không tìm thấy, $\frac{1}{\text{rank}_i} = 0$.
*   **Ý nghĩa trong RAG**: Trong các hệ thống RAG, LLM bị ảnh hưởng bởi hiện tượng **"Lost in the Middle"** (dễ bỏ qua thông tin nằm ở giữa ngữ cảnh dài). Do đó, việc đưa tài liệu đúng lên top đầu (rank 1 hoặc 2) là cực kỳ quan trọng. MRR giúp ta đánh giá chính xác khả năng sắp xếp tài liệu của Retriever; MRR càng gần 1.0 nghĩa là tài liệu liên quan nhất luôn nằm ở vị trí cao nhất.

---

### 1.2. Hệ số Đồng thuận & Cohen's Kappa trong Đa giám khảo (Multi-Judge)
*   **Hệ số đồng thuận (Agreement Rate)**: Là tỷ lệ phần trăm đơn giản số lần các Judge chấm điểm giống nhau hoặc lệch nhau trong phạm vi cho phép ($\le 1$ điểm).
*   **Cohen's Kappa ($\kappa$)**: Là chỉ số thống kê đo lường mức độ đồng thuận giữa các giám khảo (Judge) khi phân loại dữ liệu định tính, có loại trừ đi tỷ lệ đồng thuận ngẫu nhiên (agreement by chance).
*   **Ý nghĩa trong AI Evaluation**: Việc tin vào một Judge duy nhất (ví dụ: chỉ dùng GPT-4) có thể dẫn đến thiên vị hoặc không khách quan (Bias). Bằng cách triển khai **Multi-Judge** (ở đây là kết hợp `gpt-4o-mini` của OpenAI và `llama-3.3-70b-versatile` của Groq), ta tính toán được độ đồng thuận của chúng:
    *   Độ đồng thuận cao (> 80%): Đảm bảo bộ Rubrics rõ ràng và kết quả đánh giá có độ tin cậy cực cao.
    *   Độ đồng thuận thấp: Cảnh báo bộ Rubrics chưa rõ ràng hoặc một trong các mô hình Judge đang gặp lỗi/ảo giác, kích hoạt bộ phân xử thứ 3 (Calibration) để đảm bảo tính khách quan.

---

### 1.3. Thiên vị Vị trí (Position Bias) và cách khắc phục
*   **Định nghĩa**: Thiên vị vị trí xảy ra khi các mô hình LLM Judge có xu hướng ưu ái hoặc chấm điểm cao hơn cho các tài liệu/câu trả lời nằm ở một vị trí cụ thể trong Prompt (ví dụ: thường chọn câu trả lời đầu tiên làm câu trả lời tốt hơn).
*   **Cách khắc phục**:
    *   **Tráo đổi vị trí (Input Swapping)**: Đổi chỗ thông tin đầu vào (ví dụ: Đánh giá Answer A vs Answer B, sau đó đánh giá ngược lại Answer B vs Answer A). Nếu điểm số thay đổi đáng kể sau khi tráo, hệ thống sẽ phát hiện ra sự thiên vị vị trí.
    *   **Kiểm soát nhiệt độ (Temperature = 0)**: Đảm bảo tính nhất quán (deterministic) cao nhất của câu trả lời.
    *   **Prompting chặt chẽ**: Yêu cầu Judge giải trình lý do trước khi đưa ra điểm số (Chain of Thought) để tránh LLM đưa ra điểm số cảm tính theo vị trí.

---

### 1.4. Đánh đổi giữa Chi phí (Cost) và Chất lượng (Quality)
*   Trong sản xuất thực tế, việc chạy benchmark bằng các mô hình cực lớn như GPT-4o hay Claude 3.5 Sonnet cho hàng nghìn test cases là cực kỳ tốn kém và chậm.
*   **Giải pháp tối ưu hóa**:
    1.  **Phân tầng mô hình (Model Tiering)**: Sử dụng các mô hình nhỏ, rẻ (như `gpt-4o-mini`, `llama-3-8b`) để đánh giá các câu hỏi dạng Fact-check đơn giản. Chỉ sử dụng các mô hình lớn (hoặc Judge thứ 3) làm Tie-breaker/Calibration cho những case khó hoặc khi xảy ra bất đồng ý kiến.
    2.  **Định tuyến thông minh (Query Routing)**: Lọc các câu hỏi xã giao thông thường bằng regex hoặc LLM giá rẻ (như trong nhóm Cost Efficiency) để trả lời ngay mà không cần kích hoạt RAG và Evaluation, giảm 30% lượng token lãng phí.

---

## 2. Đóng góp Kỹ thuật (Engineering Contributions)
*   Thiết kế và hoàn thiện bộ dữ liệu **Golden Dataset gồm 54 cases** bao phủ đầy đủ 4 nhóm lỗi khó (Adversarial, Edge Cases, Multi-turn, Technical Constraints) và ánh xạ chính xác Ground Truth file để đo đạc MRR.
*   Phát triển lớp `RetrievalEvaluator` tính toán thực tế Hit Rate và MRR.
*   Xây dựng `LLMJudge` kết nối đa nền tảng (OpenAI & Groq) song song thông qua `asyncio.gather`, triển khai thuật toán **Calibration (Hiệu chuẩn điểm số lệch bằng Judge thứ 3)** và **Position Bias Check** tự động.
*   Tích hợp chế độ mô phỏng fallback thông minh giúp hệ thống tự động phục hồi và tiếp tục chạy khi gặp lỗi Rate Limit 429 hoặc thiếu API Key.
