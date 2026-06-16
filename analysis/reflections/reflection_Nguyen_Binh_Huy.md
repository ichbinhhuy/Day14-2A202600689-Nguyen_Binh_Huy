# Báo cáo Thu hoạch Cá nhân

**Sinh viên:** Nguyễn Binh Huy  
**Mã sinh viên:** 2A202600689  

---

## 1. Tìm hiểu các Khái niệm Kỹ thuật

### 1.1. Mean Reciprocal Rank (MRR)
*   **Khái niệm**: MRR là chỉ số đánh giá khả năng tìm kiếm tài liệu của hệ thống. Nó đo xem tài liệu đúng đầu tiên nằm ở vị trí thứ mấy trong kết quả trả về.
*   **Công thức**:
    $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
    Trong đó: $|Q|$ là tổng số câu hỏi, $\text{rank}_i$ là thứ tự của tài liệu đúng đầu tiên trong kết quả của câu hỏi thứ $i$. Nếu không tìm thấy, giá trị là 0.
*   **Ý nghĩa**: Trong RAG, nếu tài liệu đúng nằm ở cuối hoặc giữa ngữ cảnh dài, mô hình đọc có thể bỏ sót thông tin. MRR càng cao (gần 1.0) nghĩa là tài liệu cần tìm càng được xếp ở vị trí đầu tiên.

### 1.2. Đa giám khảo (Multi-Judge), Độ đồng thuận và Cohen's Kappa
*   **Hệ số đồng thuận (Agreement Rate)**: Là tỷ lệ số lần các giám khảo (Judge) cho điểm giống nhau hoặc chỉ lệch nhau tối đa 1 điểm.
*   **Cohen's Kappa**: Là chỉ số thống kê đo lường độ đồng thuận giữa các Judge, loại trừ đi yếu tố ngẫu nhiên (trùng hợp ngẫu nhiên). Chỉ số này dao động từ -1 đến 1; giá trị càng gần 1.0 thể hiện các Judge đồng thuận thực chất và đáng tin cậy.
*   **Ý nghĩa**: Khi đánh giá câu trả lời của AI, việc chỉ dùng 1 mô hình làm Judge dễ bị lệch. Kết hợp 2 mô hình (như GPT-4o-mini và Llama-3.3) giúp đánh giá khách quan hơn. Nếu 2 mô hình lệch nhau quá nhiều (trên 1 điểm), ta cần dùng mô hình thứ 3 làm trọng tài (Calibration) để quyết định điểm cuối cùng.

### 1.3. Thiên vị Vị trí (Position Bias) và cách khắc phục
*   **Định nghĩa**: LLM Judge thường có xu hướng chấm điểm cao hơn cho câu trả lời xuất hiện ở vị trí đầu tiên trong prompt.
*   **Cách khắc phục**:
    *   **Tráo đổi vị trí**: Đảo ngược thứ tự các câu trả lời để chấm điểm lần hai, sau đó so sánh kết quả.
    *   **Đặt Temperature = 0**: Giúp mô hình chấm điểm ổn định và ít ngẫu nhiên hơn.
    *   **Chain of Thought**: Yêu cầu mô hình giải thích lý do trước khi chấm điểm để hạn chế chấm theo cảm tính.

### 1.4. Đánh đổi giữa Chi phí (Cost) và Chất lượng (Quality)
*   Sử dụng các mô hình lớn để đánh giá sẽ tốn nhiều chi phí API và thời gian.
*   **Cách tối ưu**:
    *   Sử dụng mô hình nhỏ và rẻ (như GPT-4o-mini) cho các câu hỏi dễ hoặc phân tích ban đầu. Chỉ dùng mô hình lớn làm trọng tài khi có bất đồng lớn giữa các Judge.
    *   Dùng bộ lọc Regex hoặc mô hình rẻ để trả lời ngay các câu chào hỏi xã giao, tránh đưa vào luồng RAG và đánh giá phức tạp.

---

## 2. Phần công việc đã thực hiện
*   Tạo file dữ liệu `golden_set.jsonl` gồm 56 câu hỏi mẫu về luật phòng chống ma túy.
*   Viết code trong `engine/retrieval_eval.py` để tính toán Hit Rate và MRR.
*   Viết logic đa giám khảo trong `engine/llm_judge.py` gọi song song GPT-4o-mini và Llama-3.3, xử lý bất đồng điểm số bằng mô hình thứ 3.
*   Thực hiện chạy thử nghiệm so sánh kết quả giữa Agent V1 (không có Reranking, câu trả lời bị rút gọn) và Agent V2 (sử dụng Reranking đầy đủ và câu trả lời hoàn thiện).
