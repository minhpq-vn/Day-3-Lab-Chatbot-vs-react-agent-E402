"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
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
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

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
    print(f"❓ Câu hỏi: {user_query}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot Baseline trả lời:\n{response}")


def run_react_agent(test_case: dict, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails (Mốc 3).
    """
    user_query = test_case["question"]
    tc_id = test_case.get("id", "?")
    category = test_case.get("category", "")
    
    print(f"\n==================================================")
    print(f"🤖 [REACT AGENT] [TEST CASE #{tc_id}] [{category}]")
    print(f"❓ Câu hỏi: {user_query}")
    print(f"--------------------------------------------------")
    
    conversation_prompt = f"User Question: {user_query}\n"
    step = 0
    final_answer_found = False
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # 1. Gọi LLM Provider thực hiện suy luận Thought & Action
        response = provider.generate(conversation_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        
        # Cập nhật prompt tích lũy ngữ cảnh
        conversation_prompt += f"{response}\n"
        
        # 2. Kiểm tra nếu Agent xuất ra Final Answer
        if "Final Answer:" in response:
            final_answer_found = True
            print(f"\n🏁 ReAct Agent đã hoàn thành nhiệm vụ ở bước {step}!")
            break
            
        # 3. Trích xuất Action và thực thi Tool
        tool_name, args = parse_action(response)
        if tool_name:
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    obs = tool_func(*args)
                except TypeError:
                    try:
                        obs = tool_func(args[0]) if args else tool_func()
                    except Exception as e:
                        obs = f"LỖI: Truyền sai số lượng tham số cho tool '{tool_name}': {e}"
                except Exception as e:
                    obs = f"LỖI: Xảy ra lỗi khi chạy tool '{tool_name}': {e}"
            else:
                obs = f"LỖI: Tool '{tool_name}' không được đăng ký. Các tool hợp lệ gồm: {list(AVAILABLE_TOOLS.keys())}"
                
            print(f"👁️ Observation: {obs}")
            conversation_prompt += f"Observation: {obs}\n"
        else:
            if "Thought:" in response:
                obs = "LỖI: Bạn chưa đưa ra Action hợp lệ theo cú pháp Action: tên_công_cụ[tham_số] hoặc Final Answer: ..."
                print(f"👁️ Observation: {obs}")
                conversation_prompt += f"Observation: {obs}\n"
            else:
                break
                
    # 4. Phanh an toàn Guardrails ngắt lặp khi đạt MAX_ITERATIONS
    if step >= MAX_ITERATIONS and not final_answer_found:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 MỐC 3: REACT AGENT LOOP & SAFEGUARDS (ROLE 4)")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    print("\n==================================================")
    print("🚀 CHẠY KIỂM THỬ REACT AGENT LOOP (MỐC 3)")
    print("==================================================")
    for test in tests:
        run_react_agent(test, provider)
