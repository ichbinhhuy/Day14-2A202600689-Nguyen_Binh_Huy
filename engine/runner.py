import asyncio
import time
from typing import List, Dict, Any

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        
        # Token pricing (USD per 1M tokens)
        self.pricing = {
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "llama-3.3-70b-versatile": {"input": 0.590, "output": 0.790}
        }

    async def run_single_test(self, test_case: Dict, case_idx: int) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        # 1. Gọi Agent để sinh câu trả lời
        # Câu trả lời thực tế sẽ trả về contexts, answer, metadata
        response = await self.agent.query(test_case["question"])
        agent_latency = time.perf_counter() - start_time
        
        # 2. Chạy RAGAS/Retrieval metrics
        eval_start = time.perf_counter()
        ragas_scores = await self.evaluator.score(test_case, response)
        
        # 3. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"], 
            response["answer"], 
            test_case["expected_answer"]
        )
        
        # 4. Kiểm tra Position Bias cho các câu hỏi khó để nâng cao chất lượng
        position_bias = {"bias_detected": False}
        if test_case.get("metadata", {}).get("difficulty") == "hard":
            position_bias = await self.judge.check_position_bias(
                test_case["question"],
                response["answer"],
                test_case["expected_answer"]
            )
            
        total_latency = time.perf_counter() - start_time
        eval_latency = total_latency - agent_latency
        
        # 5. Ước lượng số lượng Token & Cost cho đợt gọi này
        # (Nếu ở chế độ mô phỏng hoặc gọi thật, ta tính dựa trên text length làm proxy nếu không có token thực)
        agent_tokens = response.get("metadata", {}).get("tokens_used", 150)
        
        # Judge prompts chứa khoảng 800-1000 input tokens và sinh ra khoảng 80-120 output tokens
        judge_in_tokens = 900
        judge_out_tokens = 100
        
        # Tính chi phí USD
        cost_gpt = (judge_in_tokens * self.pricing["gpt-4o-mini"]["input"] / 1_000_000) + \
                   (judge_out_tokens * self.pricing["gpt-4o-mini"]["output"] / 1_000_000)
                   
        cost_llama = (judge_in_tokens * self.pricing["llama-3.3-70b-versatile"]["input"] / 1_000_000) + \
                     (judge_out_tokens * self.pricing["llama-3.3-70b-versatile"]["output"] / 1_000_000)
                     
        total_cost = cost_gpt + cost_llama
        
        # Nếu có bước calibration (Judge 3), cộng thêm cost
        if judge_result.get("agreement_rate", 1.0) == 0.4:
            total_cost += cost_gpt # Judge 3 gọi thêm gpt-4o-mini
            
        print(f"  [{case_idx}] Done: {test_case['question'][:40]}... "
              f"| Score: {judge_result['final_score']:.1f} "
              f"| Latency: {total_latency:.2f}s "
              f"| Cost: ${total_cost:.5f}")
              
        return {
            "test_case_id": case_idx,
            "question": test_case["question"],
            "agent_response": response["answer"],
            "expected_answer": test_case["expected_answer"],
            "latency": {
                "agent_latency": agent_latency,
                "eval_latency": eval_latency,
                "total_latency": total_latency
            },
            "tokens": {
                "agent_tokens": agent_tokens,
                "eval_input_tokens": judge_in_tokens * 2,
                "eval_output_tokens": judge_out_tokens * 2
            },
            "cost": total_cost,
            "ragas": ragas_scores,
            "judge": judge_result,
            "position_bias": position_bias,
            "status": "fail" if judge_result["final_score"] < 3.0 else "pass"
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size.
        Thêm một chút delay nghỉ giữa các batch để tuân thủ Rate Limit (RPM/TPM) của Groq/Gemini.
        """
        print(f"Starting benchmark for {len(dataset)} test cases...")
        results = []
        
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            print(f"-> Processing batch {i // batch_size + 1} ({len(batch)} cases)...")
            
            tasks = [self.run_single_test(case, i + idx + 1) for idx, case in enumerate(batch)]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Nếu không phải batch cuối, nghỉ 2 giây để tránh dồn ứ API Rate Limit
            if i + batch_size < len(dataset):
                await asyncio.sleep(2.0)
                
        return results
