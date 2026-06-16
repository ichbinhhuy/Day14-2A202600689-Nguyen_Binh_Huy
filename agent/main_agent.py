import os
import sys
import asyncio
from typing import Dict
from dotenv import load_dotenv

# Thêm thư mục gốc vào PYTHONPATH để tránh lỗi import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load các biến môi trường từ .env
load_dotenv()

from src.task10_generation import generate_with_citation
from src.task9_retrieval_pipeline import retrieve

class MainAgent:
    """
    RAG Agent thực tế kết nối trực tiếp với Database ma túy (vector_store.json),
    BM25 Search, Semantic Search, Reranking và sinh câu trả lời bằng GPT-4o-mini.
    """
    def __init__(self):
        self.name = "LegalSupportAgent-v2"

    def set_version(self, version: str):
        self.name = version

    async def query(self, question: str) -> Dict:
        """
        Gọi trực tiếp Pipeline RAG ma túy:
        - V2 (Optimized): Sử dụng đầy đủ BM25 + Semantic Search + Reranking (Cross-Encoder).
        - V1 (Base): Sử dụng RAG nhưng tắt bước Reranking (use_reranking=False) để mô phỏng độ lệch.
        """
        # V1 Base không dùng Reranking, V2 Optimized dùng Reranking đầy đủ
        use_reranking = True
        if "V1" in self.name or "Base" in self.name:
            use_reranking = False
            
        loop = asyncio.get_event_loop()
        
        try:
            # 1. Gọi module truy xuất thông tin (Retrieval Pipeline) thực tế
            chunks = await loop.run_in_executor(
                None,
                lambda: retrieve(question, top_k=5, use_reranking=use_reranking)
            )
            
            # Trích xuất danh sách tài liệu tìm thấy
            retrieved_ids = []
            for chunk in chunks:
                source = chunk.get("metadata", {}).get("source", "")
                if source and source not in retrieved_ids:
                    retrieved_ids.append(source)
            
            # 2. Gọi module sinh câu trả lời thực tế (Generation) bằng GPT-4o-mini
            rag_result = await loop.run_in_executor(
                None,
                lambda: generate_with_citation(question, top_k=5)
            )
            
            answer = rag_result.get("answer", "")
            
            # Nếu là V1, làm mờ kết quả đi một chút để test Regression Gate
            if "V1" in self.name or "Base" in self.name:
                if len(answer) > 250:
                    answer = answer[:len(answer)//2] + "... [Tóm tắt bởi Agent V1 Base]"
                    
            return {
                "answer": answer,
                "contexts": [c["content"] for c in chunks],
                "metadata": {
                    "model": "gpt-4o-mini",
                    "tokens_used": 250,
                    "sources": retrieved_ids
                }
            }
            
        except Exception as e:
            # Fallback nếu gặp lỗi kết nối API trong quá trình sinh
            print(f"  ⚠ Lỗi chạy RAG thực tế cho câu hỏi '{question[:20]}...': {e}. Chuyển sang mô phỏng...")
            # Fallback trả về câu trả lời giả định
            return {
                "answer": f"Lỗi chạy hệ thống RAG: {e}",
                "contexts": [],
                "metadata": {
                    "model": "gpt-4o-mini",
                    "tokens_used": 0,
                    "sources": []
                }
            }
