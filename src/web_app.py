"""
🌐 WEB APPLICATION SERVER (Flask App)
Giao diện Web tương tác trực quan cho bài Lab 3: Chatbot vs ReAct Agent.
Hỗ trợ Live Chat Studio, So sánh Side-by-Side và Chạy tự động 5 Test Cases.
"""

import json
import os
import sys
import re
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider, BaseLLMProvider

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# Biến provider toàn cục (có thể đổi động từ giao diện Web)
current_provider_name = os.getenv("LLM_PROVIDER", "gemini")
provider = get_llm_provider(current_provider_name)


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_action(text: str):
    """Trích xuất tên tool và tham số từ response của LLM"""
    if not text or not isinstance(text, str):
        return None, []
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


def run_baseline_chatbot_trace(user_query: str):
    """Chạy Chatbot Baseline và trả về kết quả cấu trúc"""
    global provider
    res = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    if not res:
        res = "[Lỗi Provider]: Không nhận được phản hồi từ LLM."
    return {
        "query": user_query,
        "response": res
    }


def run_react_agent_trace(user_query: str):
    """Chạy ReAct Agent và thu thập chi tiết chuỗi suy luận Thought -> Action -> Observation"""
    global provider
    conversation_prompt = f"User Question: {user_query}\n"
    step = 0
    final_answer_found = False
    trace_steps = []
    final_answer = ""

    while step < MAX_ITERATIONS:
        step += 1
        raw_response = provider.generate(conversation_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        if not raw_response:
            raw_response = "[Lỗi Provider]: Không nhận được phản hồi từ LLM."
            
        conversation_prompt += f"{raw_response}\n"

        # Trích xuất Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", raw_response, re.DOTALL)
        thought_text = thought_match.group(1).strip() if thought_match else raw_response.strip()

        # Kiểm tra Final Answer
        if "Final Answer:" in raw_response:
            final_answer_found = True
            fa_match = re.search(r"Final Answer:\s*(.*)", raw_response, re.DOTALL)
            final_answer = fa_match.group(1).strip() if fa_match else raw_response
            trace_steps.append({
                "step": step,
                "thought": thought_text,
                "action": None,
                "observation": None,
                "final_answer": final_answer
            })
            break

        # Trích xuất Action và thực thi Tool
        tool_name, args = parse_action(raw_response)
        obs_text = None
        action_text = None

        if tool_name:
            action_text = f"{tool_name}[{', '.join(args)}]"
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    obs_text = tool_func(*args)
                except TypeError:
                    try:
                        obs_text = tool_func(args[0]) if args else tool_func()
                    except Exception as e:
                        obs_text = f"LỖI: Truyền sai tham số cho tool '{tool_name}': {e}"
                except Exception as e:
                    obs_text = f"LỖI: Xảy ra lỗi khi chạy tool '{tool_name}': {e}"
            else:
                obs_text = f"LỖI: Tool '{tool_name}' chưa đăng ký."
            conversation_prompt += f"Observation: {obs_text}\n"

        trace_steps.append({
            "step": step,
            "thought": thought_text,
            "action": action_text,
            "observation": obs_text,
            "final_answer": None
        })

    # Nếu chưa có Final Answer thì tổng hợp lượt cuối
    if not final_answer_found:
        synthesis_prompt = conversation_prompt + "\nThought: Đã nhận được dữ liệu từ công cụ. Hãy đưa ra câu trả lời Final Answer hoàn chỉnh giải thích kết quả cho người dùng.\n"
        final_res = provider.generate(synthesis_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        if final_res and "Final Answer:" in final_res:
            fa_match = re.search(r"Final Answer:\s*(.*)", final_res, re.DOTALL)
            final_answer = fa_match.group(1).strip() if fa_match else final_res
        else:
            final_answer = final_res if final_res else "Hệ thống đã đạt giới hạn suy luận an toàn."
            
    return {
        "query": user_query,
        "steps": trace_steps,
        "final_answer": final_answer,
        "guardrail_triggered": not final_answer_found and (step >= MAX_ITERATIONS)
    }


# ==========================================
# WEB API ENDPOINTS
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_status():
    global provider, current_provider_name
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    return jsonify({
        "provider": provider.__class__.__name__,
        "provider_code": current_provider_name,
        "model_name": model_name,
        "max_iterations": MAX_ITERATIONS
    })


@app.route("/api/config", methods=["POST"])
def update_config():
    global provider, current_provider_name
    data = request.json or {}
    new_provider = data.get("provider", "mock")
    current_provider_name = new_provider
    provider = get_llm_provider(new_provider)
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    return jsonify({
        "status": "success",
        "provider": provider.__class__.__name__,
        "model_name": model_name
    })


@app.route("/api/test_cases", methods=["GET"])
def api_test_cases():
    try:
        cases = load_test_cases()
        return jsonify(cases)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json or {}
    user_query = data.get("query", "").strip()
    mode = data.get("mode", "react")  # 'react' hoặc 'baseline'
    
    if not user_query:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    if mode == "baseline":
        result = run_baseline_chatbot_trace(user_query)
    else:
        result = run_react_agent_trace(user_query)

    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def api_compare():
    data = request.json or {}
    user_query = data.get("query", "").strip()
    if not user_query:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    baseline_res = run_baseline_chatbot_trace(user_query)
    react_res = run_react_agent_trace(user_query)

    return jsonify({
        "query": user_query,
        "baseline": baseline_res,
        "react": react_res
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"==================================================")
    print(f"🏫 VINUNI AI LAB 3 WEB APP IS RUNNING AT:")
    print(f"👉 http://localhost:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)
