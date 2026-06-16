# Báo cáo Phân tích Lỗi

## 1. Tổng quan kết quả Benchmark
- **Tổng số câu hỏi đánh giá:** 54
- **Điểm trung bình Agent V1 (Base):** 3.42 / 5.0
- **Điểm trung bình Agent V2 (Optimized):** 3.51 / 5.0
- **Điểm cải thiện (Delta):** +0.09 (Chấp nhận cập nhật)
- **Tỷ lệ tìm kiếm chính xác (Hit Rate):** 77.78%
- **Tỷ lệ đồng thuận giữa các Judge (Agreement Rate):** 88.89%

### Khác biệt giữa Agent V1 (Base) và Agent V2 (Optimized)
- **Agent V1 (Base):**
  - Không sử dụng cơ chế sắp xếp lại tài liệu (Reranking). Các tài liệu lấy ra từ tìm kiếm lai (Hybrid Search) được đưa trực tiếp vào mô hình sinh mà không lọc nhiễu.
  - Câu trả lời thường bị cắt ngắn, thiếu chi tiết hoặc đôi khi bị bỏ sót thông tin quan trọng.
- **Agent V2 (Optimized):**
  - Sử dụng đầy đủ tìm kiếm lai kết hợp với Reranking (sử dụng Cross-Encoder và RRF). Điều này giúp chọn lọc các tài liệu có độ liên quan cao nhất lên đầu ngữ cảnh.
  - Câu trả lời được cải thiện đầy đủ, chính xác và bám sát tài liệu đối chiếu hơn.

---

## 2. Phân nhóm các lỗi gặp phải

| Nhóm lỗi | Số lượng | Nguyên nhân chính |
| :--- | :--- | :--- |
| **Định tuyến câu hỏi chào hỏi** | 1 | Hệ thống tự động đưa câu chào hỏi xã giao vào tìm kiếm tài liệu luật, dẫn đến câu trả lời dài dòng không cần thiết. |
| **Xử lý câu hỏi thiếu thông tin** | 1 | Người dùng hỏi về "nghệ sĩ đó" nhưng hệ thống không yêu cầu làm rõ danh tính mà tự phỏng đoán từ tài liệu. |
| **Kế thừa ngữ cảnh đa lượt** | 2 | Khả năng ghi nhớ thông tin từ câu hỏi trước của Agent chưa tốt. |

---

## 3. Phân tích nguyên nhân (Phương pháp 5 Whys)

### Trường hợp 1: Trả lời câu hỏi xã giao "Chào bạn, bạn có khỏe không?" (Case 40)
1. **Mô tả:** Điểm số nhận được rất thấp do câu trả lời quá khô khan.
2. **Tại sao 1:** Agent đưa ra câu từ chối cung cấp tư vấn pháp lý thay vì lời chào thân thiện.
3. **Tại sao 2:** Hệ thống cố gắng áp dụng tài liệu luật ma túy vào câu hỏi xã giao thông thường.
4. **Tại sao 3:** Bộ tìm kiếm tài liệu (RAG) cố nạp tài liệu không liên quan làm ngữ cảnh.
5. **Tại sao 4:** Bộ phân loại câu hỏi (Router) hoạt động sai, chuyển hướng nhầm câu hỏi chào hỏi vào luồng tra cứu luật.
6. **Nguyên nhân gốc:** Chưa có bộ lọc nhanh (Greeting Router) ở đầu vào để xử lý riêng các câu xã giao mà không cần tìm kiếm tài liệu.

### Trường hợp 2: Trả lời câu hỏi mập mờ "Nghệ sĩ đó bị bắt ở đâu?" (Case 53)
1. **Mô tả:** Điểm số ở mức trung bình, có sự chênh lệch lớn giữa các mô hình Judge.
2. **Tại sao 1:** Agent tự phỏng đoán thông tin để trả lời thay vì hỏi lại người dùng.
3. **Tại sao 2:** Hệ thống không nhận biết được từ "nghệ sĩ đó" là ai (trong tài liệu có nhiều nghệ sĩ khác nhau).
4. **Tại sao 3:** Bộ tìm kiếm trả về thông tin của tất cả các nghệ sĩ, gây nhiễu ngữ cảnh.
5. **Tại sao 4:** System prompt của Agent chỉ yêu cầu trả lời dựa trên tài liệu, không hướng dẫn cách xử lý khi thiếu thông tin cụ thể.
6. **Nguyên nhân gốc:** Thiếu logic phát hiện câu hỏi mập mờ và yêu cầu người dùng làm rõ trước khi trả lời.

---

## 4. Hướng khắc phục đề xuất
- Thêm bộ lọc nhanh bằng từ khóa để nhận diện câu hỏi xã giao, giúp giảm chi phí gọi API.
- Điều chỉnh System Prompt để Agent biết từ chối phỏng đoán và hỏi lại khi câu hỏi của người dùng bị thiếu thông tin rõ ràng.
- Sử dụng thêm cơ chế sắp xếp lại tài liệu (Reranking) để lọc bớt thông tin gây nhiễu trước khi đưa vào mô hình trả lời.
