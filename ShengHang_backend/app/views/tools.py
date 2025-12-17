# 存储各种工具方法
from django.http import JsonResponse
import hashlib

# ================================
# 工具函数
# ================================
# 密码哈希
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

# 中文输出
def json_cn(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})

# 管理员权限检查
def require_admin(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return False, json_cn({"error": "请先登录"}, 403)

    if user_id != 1:
        return False, json_cn({"error": "不是管理员"}, 403)

    return True, None

def get_user_id(request):
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return json_cn({"error": "用户未登录"}, 403)

# ============================================================
# 辅助工具：将游标结果转换为字典列表
# ============================================================
def dictfetchall(cursor):
    "将游标返回的结果转换为字典"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# 把秒转成 mm:ss 格式
def format_time(sec):
    return f"{sec // 60}:{sec % 60:02d}"
