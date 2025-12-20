# 存储各种工具方法
import datetime
from django.db import connection
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
ADMIN_USER_ID = 1  # 可以改成实际管理员 id
def require_admin(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return False, json_cn({"error": "请先登录"}, 403)

    if user_id != ADMIN_USER_ID:
        return False, json_cn({"error": "不是管理员"}, 403)

    return True, None

def get_user_id(request):
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return json_cn({"error": "用户未登录"}, 403)
    return current_user_id

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
    if sec is None:
        return "0:00"
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"

# 通用日志记录函数
def add_system_log(action, target_table=None, target_id=None, result='success'):
    """
    :param action: 操作具体内容，如 "添加歌手: 周杰伦"
    :param target_table: 操作的表名，如 "Singer"
    :param target_id: 操作的记录ID，如 10
    :param result: 'success' 或 'fail'
    """
    try:
        sql = """
              INSERT INTO SystemLog (action, target_table, target_id, result, action_time)
              VALUES (%s, %s, %s, %s, %s) \
              """
        now = datetime.datetime.now()

        # 使用一个新的 cursor，防止干扰外部事务
        with connection.cursor() as cursor:
            cursor.execute(sql, [action, target_table, target_id, result, now])

    except Exception as e:
        # 日志记录失败不应该影响主业务流程，所以这里只打印错误，不抛出异常
        print(f"日志记录失败: {e}")