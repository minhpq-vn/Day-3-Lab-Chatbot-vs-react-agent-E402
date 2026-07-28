"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Hỗ trợ cả chế độ Tương tác trực tiếp (Interactive CLI Chatbot) và Chạy tự động bộ Test Cases.
"""

import json
import os
import sys
import re
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from agent_safety import (
    execute_safe_tool,
    extract_safe_final_answer,
    prepare_user_query,
    redact_sensitive_text,
)

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_action(text: str):
    """
    Trích xuất tên tool và danh sách tham số từ chuỗi trả về của LLM.
    Định dạng kỳ vọng: Action: tên_công_cụ[tham_số_1, tham_số_2] hoặc Action: tên_công_cụ(tham_số_1)
    """
    pattern = r"Action:\s*([a-zA-Z0-9_]+)[\[\(](.*?)[\]\)]"
    match = re.search(pattern, text)
    if not match:
        return None, []
    
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        return tool_name, []
        
    args = [arg.strip().strip("'\"") for arg in raw_args.split(",") if arg.strip()]
    return tool_name, args


def run_baseline_chatbot(test_case: dict, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Chạy từng test case từ config/test_cases.json và in ra kết quả.
    """
    user_query = test_case["question"]
    tc_id = test_case.get("id", "?")
    category = test_case.get("category", "")
    
    print(f"\n--------------------------------------------------")
    print(f"💬 [CHATBOT BASELINE] [TEST CASE #{tc_id}] [{category}]")
    print(f"❓ Câu hỏi: {redact_sensitive_text(user_query)}")

    safe_query, refusal = prepare_user_query(user_query)
    if refusal:
        print(f"🤖 Chatbot Baseline trả lời:\n{refusal[1]}")
        return
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(safe_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot Baseline trả lời:\n{response}")


def run_react_agent(test_case: dict, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    user_query = test_case["question"]
    tc_id = test_case.get("id", "?")
    category = test_case.get("category", "")
    
    print(f"\n==================================================")
    print(f"🤖 [REACT AGENT] [TEST CASE #{tc_id}] [{category}]")
    print(f"❓ Câu hỏi: {redact_sensitive_text(user_query)}")
    print(f"--------------------------------------------------")

    safe_query, refusal = prepare_user_query(user_query)
    if refusal:
        print(f"👁️ Observation: [{refusal[0]}] {refusal[1]}")
        print(f"\n🏁 ReAct Agent đã dừng an toàn: {refusal[1]}")
        return
    
    conversation_prompt = f"User Question: {safe_query}\n"
    step = 0
    final_answer_found = False
    executed_actions = set()
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # 1. Gọi LLM Provider thực hiện suy luận Thought & Action
        response = provider.generate(conversation_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        # Cập nhật prompt tích lũy ngữ cảnh
        conversation_prompt += f"{response}\n"
        
        # 2. Kiểm tra nếu Agent xuất ra Final Answer
        final_answer = extract_safe_final_answer(response)
        if final_answer:
            final_answer_found = True
            print(f"Final Answer: {final_answer}")
            print(f"\n🏁 ReAct Agent đã hoàn thành nhiệm vụ ở bước {step}!")
            break
        if "Final Answer:" in response:
            print("🛡️ GUARDRAIL TRIGGERED: Final Answer không hợp lệ hoặc chứa thông tin nhạy cảm.")
            break
            
        # 3. Trích xuất Action và thực thi Tool
        tool_name, args = parse_action(response)
        if tool_name:
            print(f"🔧 Action: {tool_name}[{', '.join(args)}]")
            obs = execute_safe_tool(tool_name, args, executed_actions)
            print(f"👁️ Observation: {obs}")
            conversation_prompt += f"Observation: {obs}\n"
        else:
            if "Thought:" in response:
                obs = "LỖI: Bạn chưa đưa ra Action hợp lệ theo cú pháp Action: tên_công_cụ[tham_số] hoặc Final Answer: ..."
                print(f"👁️ Observation: {obs}")
                conversation_prompt += f"Observation: {obs}\n"
            else:
                break
                
    # 4. Phanh an toàn Guardrails hoặc Lượt tổng hợp Final Answer sau Observation cuối cùng
    if not final_answer_found:
        print("\n📝 [TỔNG HỢP FINAL ANSWER SAU OBSERVATION CUỐI]")
        synthesis_prompt = conversation_prompt + "\nThought: Đã nhận được dữ liệu từ công cụ. Hãy đưa ra câu trả lời Final Answer hoàn chỉnh giải thích kết quả cho người dùng.\n"
        final_res = provider.generate(synthesis_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        final_answer = extract_safe_final_answer(final_res)
        if final_answer:
            print(f"Final Answer: {final_answer}")
            print("\n🏁 ReAct Agent đã hoàn thành tổng hợp câu trả lời cuối cùng!")
        else:
            print(f"\n🛡️ GUARDRAIL TRIGGERED: Không thể tạo câu trả lời an toàn sau tối đa {MAX_ITERATIONS} bước.")


def run_interactive_agent(provider):
    """
    Chế độ Chatbot tương tác trực tiếp qua Console CLI (Interactive Mode).
    Người dùng tự gõ câu hỏi để ReAct Agent trả lời theo thời gian thực.
    """
    print("\n==================================================")
    print("💬 CHẾ ĐỘ CHATBOT TƯƠNG TÁC TRỰC TIẾP (INTERACTIVE CLI)")
    print("Nhập câu hỏi của bạn để chat với ReAct Agent.")
    print("Gõ 'exit', 'quit' hoặc 'q' để thoát.")
    print("==================================================")
    
    while True:
        try:
            user_query = input("\n👤 Bạn: ").strip()
            if not user_query:
                continue
            if user_query.lower() in ["exit", "quit", "q"]:
                print("👋 Cảm ơn bạn đã sử dụng Chatbot!")
                break
                
            test_case_dict = {
                "id": "CLI",
                "category": "Tương tác trực tiếp",
                "question": user_query
            }
            run_react_agent(test_case_dict, provider)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã thoát chương trình!")
            break


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 CHẾ ĐỘ CHẠY CHATBOT TƯƠNG TÁC & KIỂM THỬ (ROLE 4)")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})\n")
    
    # Kiểm tra tham số truyền vào qua command line (ví dụ: python src/app.py --test)
    if len(sys.argv) > 1 and sys.argv[1] in ["--test", "-t", "test"]:
        tests = load_test_cases()
        print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
        print("🚀 CHẠY TỰ ĐỘNG BỘ TEST CASES...")
        for test in tests:
            run_react_agent(test, provider)
    else:
        # Mặc định chạy chế độ Tương tác trực tiếp Chatbot CLI
        run_interactive_agent(provider)
