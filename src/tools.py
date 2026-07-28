"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi để tra cứu đơn hàng và xử lý đổi trả.
"""

import csv
import json
import os
from datetime import datetime, timedelta

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


# Tự động đồng bộ ngày trong CSV khi module tools được import
sync_database_dates()


def load_return_policies() -> dict:
    """Tải cấu hình chính sách đổi trả từ file JSON."""
    if not os.path.exists(POLICIES_PATH):
        # Trả về dữ liệu mặc định dự phòng nếu file không tồn tại
        return {
            "fashion": {"days": 7, "condition": "Còn nguyên tem mác, chưa qua sử dụng."},
            "electronics": {"days": 15, "condition": "Chưa kích hoạt, lỗi kỹ thuật từ nhà sản xuất."},
            "books": {"days": 3, "condition": "Không bị rách, bẩn, có kèm hóa đơn gốc."},
            "home & kitchen": {"days": 10, "condition": "Chưa qua sử dụng, đầy đủ phụ kiện và hộp."},
            "sports": {"days": 7, "condition": "Chưa qua sử dụng, còn bao bì nhãn mác nguyên vẹn."}
        }
    with open(POLICIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_order_status(order_id: str) -> str:
    """
    Tra cứu thông tin trạng thái của một đơn hàng cụ thể từ hệ thống.
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD-1001', 'ORD-1002')
        
    Returns:
        str: Chi tiết trạng thái đơn hàng (Khách hàng, sản phẩm, ngành hàng, giá trị, trạng thái giao hàng).
    """
    order_id = order_id.strip().upper()
    if not os.path.exists(CSV_PATH):
        return "LỖI: Hệ thống cơ sở dữ liệu đơn hàng (data/orders.csv) không tồn tại."
        
    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["order_id"] == order_id:
                delivery_date = row["delivery_date"]
                status = row["status"]
                delivery_info = f" (giao ngày {delivery_date})" if delivery_date else ""
                return (
                    f"Thông tin đơn hàng {order_id}:\n"
                    f"- Khách hàng: {row['customer_name']}\n"
                    f"- Sản phẩm: {row['product_name']} (Danh mục: {row['category']})\n"
                    f"- Giá trị: {row['price']} VND\n"
                    f"- Trạng thái: {status}{delivery_info}"
                )
    return f"LỖI: Không tìm thấy đơn hàng nào có mã '{order_id}' trong hệ thống."


def get_return_policy(category: str) -> str:
    """
    Tra cứu chính sách đổi trả hàng cho một danh mục sản phẩm cụ thể.
    
    Args:
        category (str): Tên danh mục (Ví dụ: 'Fashion', 'Electronics', 'Books', 'Home & Kitchen', 'Sports')
        
    Returns:
        str: Quy định đổi trả của danh mục (số ngày tối đa được đổi trả và điều kiện sản phẩm).
    """
    cat_lower = category.lower().strip()
    policies = load_return_policies()
    if cat_lower in policies:
        policy = policies[cat_lower]
        return f"Chính sách đổi trả cho '{category}': Tối đa {policy['days']} ngày kể từ ngày nhận hàng thành công. Điều kiện: {policy['condition']}"
    else:
        return f"LỖI: Không tìm thấy danh mục '{category}'. Các danh mục hợp lệ gồm: {list(policies.keys())}"


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
    order_id = order_id.strip().upper()
    if not os.path.exists(CSV_PATH):
        return "LỖI: Hệ thống cơ sở dữ liệu đơn hàng (data/orders.csv) không tồn tại."
        
    # 1. Tìm thông tin đơn hàng trong database CSV
    order_row = None
    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["order_id"] == order_id:
                order_row = row
                break
                
    if not order_row:
        return f"LỖI: Không thể thực hiện đổi trả. Không tìm thấy đơn hàng '{order_id}'."
        
    # 2. Kiểm tra trạng thái đơn hàng (chỉ hỗ trợ đổi trả khi đã giao hàng)
    status = order_row["status"]
    if status != "Delivered":
        return f"TỪ CHỐI: Đơn hàng '{order_id}' hiện có trạng thái là '{status}'. Chỉ đơn hàng đã giao thành công ('Delivered') mới được hỗ trợ đổi trả."
        
    # 3. Tính toán số ngày đã trôi qua kể từ ngày giao hàng thực tế
    delivery_date_str = order_row["delivery_date"]
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
    category = order_row["category"]
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


# Danh sách các tool được đăng ký để Agent sử dụng cho Đề tài 5
AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "get_return_policy": get_return_policy,
    "request_return": request_return,
}
