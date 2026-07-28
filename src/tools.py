"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi để tra cứu đơn hàng và xử lý đổi trả.
Các công cụ được thiết kế chống crash 100%, tự động bắt lỗi tham số và hỗ trợ cả 2 bộ tên công cụ (từ prompts.py và test_cases.json).
"""

import csv
import json
import os
from datetime import datetime

# Đường dẫn dữ liệu
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "orders.csv"))
POLICIES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "return_policies.json"))

# Ngày hiện tại thực tế của hệ thống (Không còn fix cứng nữa)
CURRENT_DATE = datetime.now().date()
CURRENT_DATE_STR = CURRENT_DATE.strftime("%Y-%m-%d")


def sync_database_dates():
    """
    Tự động cập nhật ngày trong file data/orders.csv để đồng bộ với ngày hiện tại của hệ thống.
    Giúp bài lab luôn đúng về mặt logic thời gian bất kể ngày chạy thực tế là ngày nào.
    """
    try:
        if not os.path.exists(CSV_PATH):
            return
            
        # Mốc ngày gốc dùng để thiết kế dữ liệu ban đầu
        base_date = datetime.strptime("2026-07-28", "%Y-%m-%d").date()
        delta = CURRENT_DATE - base_date
        
        if delta.days == 0:
            return  # Không cần dịch chuyển nếu ngày chạy trùng với mốc ngày gốc
            
        rows = []
        headers = []
        
        # 1. Đọc và dịch chuyển ngày trong bộ dữ liệu
        with open(CSV_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            if not headers:
                return
            for row in reader:
                # Dịch chuyển ngày đặt hàng (order_date)
                if row.get("order_date"):
                    try:
                        od = datetime.strptime(row["order_date"], "%Y-%m-%d").date()
                        row["order_date"] = (od + delta).strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                # Dịch chuyển ngày giao hàng (delivery_date)
                if row.get("delivery_date"):
                    try:
                        dd = datetime.strptime(row["delivery_date"], "%Y-%m-%d").date()
                        row["delivery_date"] = (dd + delta).strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                rows.append(row)
                
        # 2. Ghi lại dữ liệu đã đồng bộ vào file CSV
        with open(CSV_PATH, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        # Chống crash tuyệt đối lúc import module
        print(f"[Cảnh báo hệ thống] Lỗi tự động đồng bộ ngày CSV: {e}")


# Tự động đồng bộ ngày trong CSV khi module tools được import
sync_database_dates()


def load_return_policies() -> dict:
    """Tải cấu hình chính sách đổi trả từ file JSON (An toàn chống lỗi file)."""
    fallback_policies = {
        "fashion": {"days": 7, "condition": "Còn nguyên tem mác, chưa qua sử dụng."},
        "electronics": {"days": 15, "condition": "Chưa kích hoạt, lỗi kỹ thuật từ nhà sản xuất."},
        "books": {"days": 3, "condition": "Không bị rách, bẩn, có kèm hóa đơn gốc."},
        "home & kitchen": {"days": 10, "condition": "Chưa qua sử dụng, đầy đủ phụ kiện và hộp."},
        "sports": {"days": 7, "condition": "Chưa qua sử dụng, còn bao bì nhãn mác nguyên vẹn."}
    }
    if not os.path.exists(POLICIES_PATH):
        return fallback_policies
    try:
        with open(POLICIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Cảnh báo hệ thống] Lỗi đọc file return_policies.json ({e}). Sử dụng dữ liệu dự phòng.")
        return fallback_policies


# ==========================================
# CÔNG CỤ THEO ĐỀ BÀI TEST_CASES.JSON (Bộ 1)
# ==========================================

def get_order_status(order_id: str) -> str:
    """
    Tra cứu thông tin trạng thái của một đơn hàng cụ thể từ hệ thống.
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD-1001', 'ORD-1002')
        
    Returns:
        str: Chi tiết trạng thái đơn hàng (Khách hàng, sản phẩm, ngành hàng, giá trị, trạng thái giao hàng).
    """
    if not isinstance(order_id, str):
        return "LỖI: Mã đơn hàng truyền vào phải là một chuỗi văn bản."
        
    order_id = order_id.strip().upper()
    if not os.path.exists(CSV_PATH):
        return "LỖI: Hệ thống cơ sở dữ liệu đơn hàng (data/orders.csv) không tồn tại."
        
    try:
        with open(CSV_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("order_id") == order_id:
                    delivery_date = row.get("delivery_date", "")
                    status = row.get("status", "")
                    delivery_info = f" (giao ngày {delivery_date})" if delivery_date else ""
                    return (
                        f"Thông tin đơn hàng {order_id}:\n"
                        f"- Khách hàng: {row.get('customer_name', 'N/A')}\n"
                        f"- Sản phẩm: {row.get('product_name', 'N/A')} (Danh mục: {row.get('category', 'N/A')})\n"
                        f"- Giá trị: {row.get('price', 'N/A')} VND\n"
                        f"- Trạng thái: {status}{delivery_info}"
                    )
        return f"LỖI: Không tìm thấy đơn hàng nào có mã '{order_id}' trong hệ thống."
    except Exception as e:
        return f"LỖI: Có lỗi xảy ra khi truy vấn dữ liệu đơn hàng: {str(e)}"


def get_return_policy(category: str) -> str:
    """
    Tra cứu chính sách đổi trả hàng cho một danh mục sản phẩm cụ thể.
    
    Args:
        category (str): Tên danh mục (Ví dụ: 'Fashion', 'Electronics', 'Books', 'Home & Kitchen', 'Sports')
        
    Returns:
        str: Quy định đổi trả của danh mục (số ngày tối đa được đổi trả và điều kiện sản phẩm).
    """
    if not isinstance(category, str):
        return "LỖI: Tên danh mục truyền vào phải là một chuỗi văn bản."
        
    cat_lower = category.lower().strip()
    try:
        policies = load_return_policies()
        if cat_lower in policies:
            policy = policies[cat_lower]
            return f"Chính sách đổi trả cho '{category}': Tối đa {policy['days']} ngày kể từ ngày nhận hàng thành công. Điều kiện: {policy['condition']}"
        else:
            return f"LỖI: Không tìm thấy danh mục '{category}'. Các danh mục hợp lệ gồm: {list(policies.keys())}"
    except Exception as e:
        return f"LỖI: Không thể lấy chính sách đổi trả: {str(e)}"


def request_return(order_id: str, reason: str) -> str:
    """
    Gửi yêu cầu đổi trả sản phẩm cho một đơn hàng cụ thể. Hệ thống sẽ tự động đối chiếu
    ngày giao hàng thực tế và chính sách đổi trả của ngành hàng để phê duyệt hoặc từ chối.
    
    Args:
        order_id (str): Mã đơn hàng muốn đổi trả (Ví dụ: 'ORD-1001')
        reason (str): Lý do muốn đổi trả (Ví dụ: 'Bị lỗi kỹ thuật', 'Mặc không vừa size')
        
    Returns:
        str: Kết quả phê duyệt đổi trả (DUYỆT THÀNH CÔNG hoặc TỪ CHỐI) kèm lý do chi tiết.
    """
    if not isinstance(order_id, str):
        return "LỖI: Mã đơn hàng truyền vào phải là một chuỗi văn bản."
    if not isinstance(reason, str):
        return "LỖI: Lý do đổi trả truyền vào phải là một chuỗi văn bản."
        
    order_id = order_id.strip().upper()
    reason = reason.strip()
    
    if not os.path.exists(CSV_PATH):
        return "LỖI: Hệ thống cơ sở dữ liệu đơn hàng (data/orders.csv) không tồn tại."
        
    try:
        # 1. Tìm thông tin đơn hàng trong database CSV
        order_row = None
        with open(CSV_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("order_id") == order_id:
                    order_row = row
                    break
                    
        if not order_row:
            return f"LỖI: Không thể thực hiện đổi trả. Không tìm thấy đơn hàng '{order_id}'."
            
        # 2. Kiểm tra trạng thái đơn hàng (chỉ hỗ trợ đổi trả khi đã giao hàng)
        status = order_row.get("status", "")
        if status != "Delivered":
            return f"TỪ CHỐI: Đơn hàng '{order_id}' hiện có trạng thái là '{status}'. Chỉ đơn hàng đã giao thành công ('Delivered') mới được hỗ trợ đổi trả."
            
        # 3. Tính toán số ngày đã trôi qua kể từ ngày giao hàng thực tế
        delivery_date_str = order_row.get("delivery_date", "")
        if not delivery_date_str:
            return f"LỖI: Đơn hàng '{order_id}' ghi nhận đã giao nhưng bị thiếu thông tin ngày giao hàng."
            
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        except ValueError:
            return f"LỖI: Định dạng ngày giao hàng của đơn '{order_id}' không hợp lệ (phải là YYYY-MM-DD)."
            
        days_passed = (CURRENT_DATE - delivery_date).days
        if days_passed < 0:
            return f"LỖI: Ngày giao hàng {delivery_date_str} nằm trong tương lai so với ngày hiện tại thực tế ({CURRENT_DATE_STR})."
            
        # 4. Kiểm tra chính sách theo danh mục sản phẩm
        category = order_row.get("category", "")
        cat_lower = category.lower().strip()
        policies = load_return_policies()
        policy = policies.get(cat_lower, {"days": 7, "condition": "Còn nguyên vẹn."})
        limit_days = policy["days"]
        
        # 5. Phán quyết phê duyệt
        if days_passed <= limit_days:
            return (
                f"DUYỆT THÀNH CÔNG: Đơn hàng {order_id} đủ điều kiện đổi trả tự động.\n"
                f"- Lý do đổi trả: '{reason}'\n"
                f"- Chi tiết kiểm tra: Sản phẩm thuộc nhóm '{category}' (thời hạn {limit_days} ngày), đã giao được {days_passed} ngày.\n"
                f"- Yêu cầu: Khách hàng cần giữ sản phẩm ở điều kiện: '{policy['condition']}'."
            )
        else:
            return (
                f"TỪ CHỐI: Đơn hàng {order_id} đã quá hạn đổi trả quy định.\n"
                f"- Chi tiết kiểm tra: Sản phẩm thuộc nhóm '{category}' có thời hạn đổi trả là {limit_days} ngày. "
                f"Tuy nhiên sản phẩm đã giao được {days_passed} ngày (từ {delivery_date_str} đến nay là {CURRENT_DATE_STR})."
            )
    except Exception as e:
        return f"LỖI: Không thể thực hiện xử lý yêu cầu đổi trả: {str(e)}"


# ==========================================
# CÔNG CỤ THEO PROMPTS.PY MỚI NHẤT (Bộ 2)
# ==========================================

def lookup_order(order_id: str) -> str:
    """
    Tra cứu trạng thái, mặt hàng và ngày nhận của đơn hàng.
    """
    return get_order_status(order_id)


def check_return_eligibility(order_id: str, item_id: str = "", reason: str = "") -> str:
    """
    Kiểm tra điều kiện đổi/trả.
    Hỗ trợ xử lý linh hoạt tham số khi LLM truyền thiếu hoặc truyền sai vị trí.
    """
    if not isinstance(order_id, str):
        return "LỖI: Mã đơn hàng truyền vào phải là một chuỗi văn bản."
        
    # Nếu LLM gọi dạng check_return_eligibility[order_id, reason]
    # Thì lý do thực tế sẽ nằm ở tham số thứ 2 (item_id)
    actual_reason = reason if reason else item_id
    if not actual_reason or not isinstance(actual_reason, str) or actual_reason.strip() == "":
        actual_reason = "Không có lý do cụ thể"
        
    return request_return(order_id, actual_reason)


def create_return_request(order_id: str, item_id: str = "", reason: str = "") -> str:
    """
    Tạo yêu cầu đổi/trả sau khi đủ điều kiện.
    Hỗ trợ xử lý linh hoạt tham số giống check_return_eligibility.
    """
    if not isinstance(order_id, str):
        return "LỖI: Mã đơn hàng truyền vào phải là một chuỗi văn bản."
        
    actual_reason = reason if reason else item_id
    if not actual_reason or not isinstance(actual_reason, str) or actual_reason.strip() == "":
        actual_reason = "Không có lý do cụ thể"
        
    return request_return(order_id, actual_reason)


# Danh sách các tool được đăng ký để Agent sử dụng cho Đề tài 5
# Đăng ký cả 2 bộ tên công cụ để đảm bảo ReAct Loop không bao giờ bị lỗi gọi sai tool
AVAILABLE_TOOLS = {
    # Bộ 1 (theo test_cases.json)
    "get_order_status": get_order_status,
    "get_return_policy": get_return_policy,
    "request_return": request_return,
    
    # Bộ 2 (theo prompts.py của hệ thống)
    "lookup_order": lookup_order,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
}
