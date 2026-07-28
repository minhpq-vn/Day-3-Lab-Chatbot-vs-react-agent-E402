"""Runtime guardrails dùng chung cho các giao diện Role 4."""

import inspect
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from prompts import TIMEOUT_SECONDS, TOOL_FAILURE_MODES
from tools import AVAILABLE_TOOLS, tool_error

SAFE_REFUSAL = "Xin lỗi, tôi không thể xử lý yêu cầu về thông tin cấu hình, thông tin xác thực hoặc hướng dẫn nội bộ."
INJECTION_REFUSAL = "Tôi không thể làm theo yêu cầu ghi đè hướng dẫn hệ thống. Vui lòng gửi yêu cầu hỗ trợ đơn hàng theo cách thông thường."

SECRET_PATTERN = re.compile(
    r"\b(api[ _-]?key|access[ _-]?token|secret|password|mật[ _-]?khẩu|otp|"
    r"system[ _-]?prompt|hướng dẫn nội bộ|biến môi trường|mã nguồn)\b", re.IGNORECASE
)
INJECTION_PATTERN = re.compile(
    r"(bỏ qua.*hướng dẫn|ignore.*(previous|instruction)|developer mode|debug mode|"
    r"đóng vai.*system|override.*instruction)", re.IGNORECASE
)
ORDER_ID_PATTERN = re.compile(r"\bORD-\d{4,}\b", re.IGNORECASE)


def classify_unsafe_request(text: str) -> str | None:
    """Phân loại input trước khi gửi tới model hoặc tool."""
    if SECRET_PATTERN.search(text):
        return "secret_request"
    if INJECTION_PATTERN.search(text):
        return "prompt_injection"
    return None


def redact_sensitive_text(text: str) -> str:
    """Không phản chiếu token/mật khẩu trong log, trace hay phản hồi API."""
    if not isinstance(text, str):
        return ""
    # Không cố che từng từ khóa: phần giá trị đứng sau (ví dụ API key) vẫn có thể
    # bị lộ. Với chuỗi nhạy cảm, thay toàn bộ nội dung bằng thông báo an toàn.
    if SECRET_PATTERN.search(text):
        return "[NỘI DUNG NHẠY CẢM ĐÃ ĐƯỢC ẨN]"
    return text


def safe_refusal_for(user_query: str) -> tuple[str, str] | None:
    code = classify_unsafe_request(user_query)
    if code == "secret_request":
        return code, SAFE_REFUSAL
    if code == "prompt_injection":
        return code, INJECTION_REFUSAL
    return None


def prepare_user_query(user_query: str) -> tuple[str | None, tuple[str, str] | None]:
    """Tách yêu cầu nghiệp vụ hợp lệ khỏi prompt injection trước khi gọi LLM.

    Injection kèm mã đơn vẫn được phép tra cứu *trạng thái* đơn. Các thao tác có
    side-effect (hoàn tiền/đổi trả) không được giữ lại từ nội dung không đáng tin.
    """
    refusal = safe_refusal_for(user_query)
    if not refusal:
        return user_query, None
    if refusal[0] == "prompt_injection":
        order_match = ORDER_ID_PATTERN.search(user_query)
        if order_match:
            order_id = order_match.group(0).upper()
            return (
                f"Hãy tra cứu trạng thái đơn hàng {order_id}. "
                "Chỉ cung cấp dữ liệu từ hệ thống; không tạo yêu cầu đổi trả hoặc hoàn tiền.",
                None,
            )
    return None, refusal


def extract_safe_final_answer(response: str) -> str | None:
    """Chỉ chấp nhận Final Answer rõ ràng và không chứa thông tin nhạy cảm."""
    match = re.search(r"(?:^|\n)Final Answer:\s*(.+)", response or "", re.DOTALL)
    if not match:
        return None
    answer = match.group(1).strip()
    if not answer or SECRET_PATTERN.search(answer):
        return None
    return answer


def execute_safe_tool(tool_name: str, args: list[str], executed_actions: set[tuple]) -> str:
    """Allowlist, kiểm tra arity, chống lặp và timeout trước khi chạy tool."""
    action_key = (tool_name, *args)
    if action_key in executed_actions:
        return tool_error("duplicate_request", "Không lặp lại cùng thao tác với cùng tham số.")
    executed_actions.add(action_key)

    tool_func = AVAILABLE_TOOLS.get(tool_name)
    if tool_func is None:
        return tool_error("unknown_tool")
    try:
        inspect.signature(tool_func).bind(*args)
    except TypeError:
        return tool_error("malformed_arguments", f"Tham số không hợp lệ cho tool '{tool_name}'.")

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool_func, *args)
    try:
        return future.result(timeout=TIMEOUT_SECONDS)
    except TimeoutError:
        future.cancel()
        return tool_error("timeout")
    except Exception:
        return tool_error("service_error")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
