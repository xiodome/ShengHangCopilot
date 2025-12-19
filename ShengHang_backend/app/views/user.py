# 用户管理模块
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import datetime
import json
from .tools import *




# ================================
# 1. 用户注册
# ================================
@csrf_exempt
def register(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)
    
    try:
        data = json.loads(request.body)
    except:
        data = request.POST


    # ----------------------------
    # 1. 数据获取
    # ----------------------------
    username = data.get("username")
    password = data.get("password")

    # -------- 可选字段，但要处理默认值 -------- 
    # 需要处理的所有可选字段
    optional_fields = ["gender", "birthday", "region", "email", "profile"]

    # 默认值
    defaults = {
        "gender": "其他",
        "birthday": None,
        "region": None,
        "email": None,
        "profile": None,
    }

    # 解析字段
    cleaned = {}
    for field in optional_fields:
        value = data.get(field, defaults[field])
        if value == "":
            value = defaults[field]
        cleaned[field] = value

    # 获得最终值
    gender = cleaned["gender"]
    birthday = cleaned["birthday"]
    region = cleaned["region"]
    email = cleaned["email"]
    profile = cleaned["profile"]


    # ----------------------------
    # 2. 基础校验
    # ----------------------------
    if not username or not password:
        return json_cn({"error": "请输入用户名和密码"}, 400)

    if len(username) < 4:
        return json_cn({"error": "用户名长度至少为4"}, 400)

    if len(password) < 6:
        return json_cn({"error": "密码长度至少为6"}, 400)

    # ----------------------------
    # 3. 禁止传入账号状态 status 和 register_time
    # ----------------------------
    if "status" in data:
        return json_cn({"error": "status field is not allowed"}, 400)

    if "register_time" in data:
        return json_cn({"error": "register_time cannot be set manually"}, 400)
    # ----------------------------
    # 4. 检查用户名是否已存在
    # ----------------------------
    sql_check_name = "SELECT user_id FROM User WHERE user_name = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_check_name, [username])
        if cursor.fetchone():
            return json_cn({"error": "用户名已存在"}, 400)

    # ----------------------------
    # 5. 检查邮箱是否唯一
    # ----------------------------
    if email:
        sql_check_email = "SELECT user_id FROM User WHERE email = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check_email, [email])
            if cursor.fetchone():
                return json_cn({"error": "邮箱已存在"}, 400)

    # ----------------------------
    # 6. 插入用户（使用原生 SQL）
    # ----------------------------
    hashed_pw = hash_password(password)

    sql_insert = """
        INSERT INTO User (user_name, password, gender, birthday, region, email, profile)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [
            username, hashed_pw, gender, birthday, region, email, profile
        ])
        
    return json_cn({"message": "注册成功"})



# ================================
# 2. 用户登录
# ================================
@csrf_exempt
def login(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # ----------------------------
    # 1. 数据获取
    # ----------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST
    

    username = data.get("username")
    password = hash_password(data.get("password"))


    # ----------------------------
    # 2. 数据校验
    # ----------------------------
    sql = """SELECT user_id, status FROM User WHERE user_name=%s AND password=%s"""
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [username, password])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户名或密码错误"}, 400)

    uid, status = row

    if status == "封禁中":
        return json_cn({"error": "用户封禁中"}, 403)

    request.session["user_id"] = uid

    # ----------------------------
    # 3. 特判管理员 user_id
    # ----------------------------
    if uid == ADMIN_USER_ID:
        return json_cn({
            "message": "管理员登录成功",
            "user_id": uid,
            "username": username,
            "is_admin": True
        })
    
    return json_cn({
        "message": "登录成功",
        "user_id": uid,
        "username": username,
        "is_admin": False
    })



# ================================
# 3. 用户退出
# ================================
@csrf_exempt
def logout(request):
    # ----------------------------
    # 1. 登录检查
    # ----------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "您尚未登录"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # ----------------------------
    # 2. 执行退出
    # ----------------------------  
    request.session.flush()
    return json_cn({"message": "退出成功"})




# ================================  
# 4. 用户注销
# ================================
@csrf_exempt
def delete_account(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 401)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # 兼容 JSON 和 form
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    password_raw = data.get("password")
    if not password_raw:
        return json_cn({"error": "请输入密码"}, 400)
    password = hash_password(password_raw)

    # --------------------------
    # 2. 查询用户真实密码（SQL）
    # --------------------------
    sql_get_user = "SELECT password FROM User WHERE user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_user, [user_id])
        row = cursor.fetchone()

        if not row:
            return json_cn({"error": "用户不存在"}, 404)

        real_hashed_pw = row[0]

    # --------------------------
    # 3. 校验密码
    # --------------------------
    if password != real_hashed_pw:
        return json_cn({"error": "密码错误，无法注销账号"}, 403)


    # --------------------------
    # 4. 删除用户（SQL）
    # --------------------------
    sql_delete = "DELETE FROM User WHERE user_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_delete, [user_id])

    # --------------------------
    # 5. 注销 session
    # --------------------------
    request.session.flush()

    return json_cn({"message": "账号已成功注销"})





# ================================
# 5. 修改密码
# ================================
@csrf_exempt
def change_password(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    uid = request.session.get("user_id")
    if not uid:
        return json_cn({"error": "请先登录"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    old_pw_raw = data.get("old_password")
    new_pw_raw = data.get("new_password")

    # --------------------------
    # 2. 密码校验
    # --------------------------
    if not old_pw_raw or not new_pw_raw:
        return json_cn({"error": "旧密码或新密码不能为空"}, 400)

    if len(new_pw_raw) < 6:
        return json_cn({"error": "新密码长度至少为 6 位"}, 400)

    if new_pw_raw == old_pw_raw:
        return json_cn({"error": "新密码不能与旧密码相同"}, 400)

    
    old_pw = hash_password(old_pw_raw)
    new_pw = hash_password(new_pw_raw)

    # --------------------------
    # 3. 旧密码校验
    # --------------------------
    sql_check = "SELECT user_id FROM User WHERE user_id=%s AND password=%s"
    sql_update = "UPDATE User SET password=%s WHERE user_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, old_pw])
        if not cursor.fetchone():
            return json_cn({"error": "旧密码错误"}, 403)

        cursor.execute(sql_update, [new_pw, uid])

    return json_cn({"message": "密码修改成功"})


# ================================
# 6. 个人界面
# ================================
@csrf_exempt
def profile(request, owner_id):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 403)
    
    # 判断是否为本人
    is_owner = (owner_id == user_id)

    # --------------------------
    # 2. 查询个人信息
    # --------------------------
    sql = """
        SELECT user_name, gender, birthday, region, email, profile 
        FROM User WHERE user_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [owner_id])
        row = cursor.fetchone()

        if not row:
            return json_cn({"error": "用户不存在"}, 404)

        username, gender, birthday, region, email, profile_text = row

    # --------------------------
    # 3. 处理空值
    # --------------------------
    gender = gender if gender else None
    region = region if region else None
    email = email if email else None
    profile_text = profile_text if profile_text else None
    birthday = str(birthday) if birthday else None

    # --------------------------
    # 4. 返回用户信息
    # --------------------------
    return json_cn({
        "user_id": owner_id,
        "username": username,
        "gender": gender,
        "birthday": birthday,
        "region": region,
        "email": email,
        "profile": profile_text,
        "is_owner": is_owner
    })


# ================================
# 7. 修改个人信息
# ================================
@csrf_exempt
def update_profile(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再修改个人信息"}, 403)
    uid = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST
        

    # --------------------------
    # 2. 获取新个人信息并校验
    # --------------------------   
    fields = []
    values = []
    for key in ["gender", "birthday", "email", "region", "profile"]:
        if key in data and data[key].strip() != "":  # 空字符串不更新
            if key == "gender" and data[key] not in ["男", "女", "其他"]:
                return json_cn({"error": "非法性别，只能为：男/女/其他"}, 400)
            if key == "birthday":
                try:
                    datetime.datetime.strptime(data[key], "%Y-%m-%d")
                except ValueError:
                    return json_cn({"error": "生日格式应为 YYYY-MM-DD"}, 400)
            if key == "email":
                sql_check_email = "SELECT user_id FROM User WHERE email=%s AND user_id<>%s"
                with connection.cursor() as cursor:
                    cursor.execute(sql_check_email, [data[key], uid])
                    if cursor.fetchone():
                        return json_cn({"error": "邮箱已存在"}, 400)
            fields.append(f"{key}=%s")
            values.append(data[key])

    if not fields:
        return json_cn({"error": "请输入修改信息"}, 400)

    # --------------------------
    # 3. 更新个人信息
    # --------------------------
    sql_update = f"UPDATE User SET {', '.join(fields)} WHERE user_id=%s"
    values.append(uid)

    with connection.cursor() as cursor:
        cursor.execute(sql_update, values)

    return json_cn({"message": "个人信息修改成功"})





# ================================
# 8. 关注用户
# ================================
@csrf_exempt
def follow_user(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 2. 获取目标用户名并查询
    # --------------------------
    target_user_id = data.get("user_id")

    if not target_user_id:
        return json_cn({"error": "请输入 user_id 参数"}, 400)


    sql_get_target = "SELECT 1 FROM User WHERE user_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [target_user_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    # --------------------------
    # 3. 不允许操作自己
    # --------------------------
    if int(target_user_id) == follower:
        return json_cn({"error": "不能对自己进行操作"}, 400)

    # --------------------------
    # 4. 关注逻辑
    # --------------------------
    # 检查是否已关注
    sql_check = """
        SELECT * FROM UserFollow
        WHERE follower_id=%s AND followed_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [follower, target_user_id])
        if cursor.fetchone():
            return json_cn({"error": "已关注该用户"}, 400)

    # 插入关注关系
    sql_follow = """INSERT INTO UserFollow(follower_id, followed_id) 
                    VALUES (%s, %s)"""

    with connection.cursor() as cursor:
        cursor.execute(sql_follow, [follower, target_user_id])

    return json_cn({"message": "关注成功"})



# ================================
# 9. 取关用户
# ================================ 
@csrf_exempt
def unfollow_user(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 2. 获取目标用户名并查询
    # --------------------------
    target_user_id = data.get("user_id")

    if not target_user_id:
        return json_cn({"error": "请输入 user_id 参数"}, 400)


    sql_get_target = "SELECT 1 FROM User WHERE user_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [target_user_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    # --------------------------
    # 3. 不允许操作自己
    # --------------------------
    if int(target_user_id) == follower:
        return json_cn({"error": "不能对自己进行操作"}, 400)

    # --------------------------
    # 4. 取关逻辑
    # --------------------------
    # 检查是否未关注
    sql_check = """
        SELECT * FROM UserFollow
        WHERE follower_id=%s AND followed_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [follower, target_user_id])
        if not cursor.fetchone():
            return json_cn({"error": "未关注该用户，不能取关"}, 400)

    # 删除关注关系
    sql_follow = """DELETE FROM UserFollow 
                WHERE follower_id = %s AND followed_id = %s
            """

    with connection.cursor() as cursor:
        cursor.execute(sql_follow, [follower, target_user_id])

    return json_cn({"message": "取关成功"})



# ================================
# 10. 关注歌手
# ================================
@csrf_exempt
def follow_singer(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]
    
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)
        
    try:
        data = json.loads(request.body)
    except:
        data = request.POST
    
    singer_id = data.get("singer_id")

    if not singer_id:
        return json_cn({"error": "请输入 singer_id"}, 400)


    # --------------------------
    # 2. 查找目标歌手
    # --------------------------
    sql_get_target = "SELECT 1 FROM Singer WHERE singer_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [singer_id])
        exist = cursor.fetchone()

    if not exist:
        return json_cn({"error": "目标歌手不存在"}, 404)

    # --------------------------
    # 3. 关注逻辑
    # --------------------------
    # 检查是否已关注
    sql_check = """
        SELECT * FROM SingerFollow
        WHERE user_id=%s AND singer_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [follower, singer_id])
        if cursor.fetchone():
            return json_cn({"error": "已关注该歌手"}, 400)

    # 插入关注关系
    sql_follow = """INSERT INTO SingerFollow(user_id, singer_id) 
                    VALUES (%s, %s)"""

    with connection.cursor() as cursor:
        cursor.execute(sql_follow, [follower, singer_id])

    return json_cn({"message": "关注成功"})



# ================================
# 11. 取关歌手
# ================================
@csrf_exempt
def unfollow_singer(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    follower = request.session["user_id"]
    
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)
        
    try:
        data = json.loads(request.body)
    except:
        data = request.POST
    
    singer_id = data.get("singer_id")

    if not singer_id:
        return json_cn({"error": "请输入 singer_id"}, 400)


    # --------------------------
    # 2. 查找目标歌手
    # --------------------------
    sql_get_target = "SELECT 1 FROM Singer WHERE singer_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql_get_target, [singer_id])
        exist = cursor.fetchone()

    if not exist:
        return json_cn({"error": "目标歌手不存在"}, 404)

    # --------------------------
    # 3. 取关逻辑
    # --------------------------
    # 检查是否已关注
    sql_check = """
        SELECT * FROM SingerFollow
        WHERE user_id=%s AND singer_id=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [follower, singer_id])
        if not cursor.fetchone():
            return json_cn({"error": "未关注该歌手"}, 400)

    # 删除关注关系
    sql_follow = """DELETE FROM SingerFollow
                WHERE user_id = %s AND singer_id = %s        
            """

    with connection.cursor() as cursor:
        cursor.execute(sql_follow, [follower, singer_id])

    return json_cn({"message": "取关成功"})




# ================================
# 12. 查看关注用户列表
# ================================
@csrf_exempt
def get_followings(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    login_user_id = request.session["user_id"]
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注用户列表"}, 403)

    
    # --------------------------
    # 2. 查询关注列表和总数
    # --------------------------
    sql = """
        SELECT u.user_name, u.user_id
        FROM UserFollow uf
        JOIN User u ON uf.followed_id = u.user_id
        WHERE uf.follower_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM UserFollow
        WHERE follower_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchone()[0]
    if not total_count:
        total_count = 0

    # --------------------------
    # 3. 返回关注列表和总数
    # --------------------------
    followings = [{"user_name": row[0], "user_id": row[1]} for row in rows]

    return json_cn({
        "total_count": total_count,
        "followings": followings
    })


# ================================
# 13. 查看粉丝列表
# ================================
@csrf_exempt
def get_followers(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)
    
    login_user_id = request.session.get("user_id")
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人粉丝列表"}, 403)

    # --------------------------
    # 2. 查询粉丝列表和总数
    # --------------------------
    sql = """
        SELECT u.user_name, u.user_id
        FROM UserFollow uf
        JOIN User u ON uf.follower_id = u.user_id
        WHERE uf.followed_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM UserFollow
        WHERE followed_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchone()[0]
    if not total_count:
        total_count = 0

    # --------------------------
    # 3. 返回粉丝列表和总数
    # --------------------------
    followers = [{"user_name": row[0], "user_id": row[1]} for row in rows]

    return json_cn({
        "total_count": total_count,
        "followers": followers
    })


# ================================
# 14. 查看关注歌手列表
# ================================
@csrf_exempt 
def get_followsingers(request, uid):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)
    
    login_user_id = request.session.get("user_id")
    

    if login_user_id != uid:
        return json_cn({"error": "无权限查看他人关注歌手列表"}, 403)

    # --------------------------
    # 2. 查询关注歌手列表和总数
    # --------------------------
    sql = """
        SELECT s.singer_name, s.singer_id
        FROM SingerFollow sf
        JOIN Singer s ON sf.singer_id = s.singer_id
        WHERE sf.user_id = %s
    """
    sql_count = """
        SELECT COUNT(*)
        FROM SingerFollow
        WHERE user_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid])
        rows = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute(sql_count, [uid])
        total_count = cursor.fetchone()[0]
    if not total_count:
        total_count = 0

    # --------------------------
    # 3. 返回关注歌手列表和总数
    # --------------------------
    follow_singers = [{"singer_name": row[0], "singer_id": row[1]} for row in rows]

    return json_cn({
        "total_count": total_count,
        "follow_singers": follow_singers
    })



# ================================
# 15. 查看他人信息
# ================================
@csrf_exempt
def get_user_info(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)
    
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # 解析 JSON
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 2. 根据用户名查找用户信息
    # --------------------------
    user_name = data.get("user_name")

    sql = """
        SELECT user_name, user_id
        FROM User
        WHERE user_name=%s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [user_name])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "用户不存在"}, 404)

    username, target_user_id = row

    # --------------------------
    # 3. 返回用户信息
    # --------------------------
    return json_cn({
        "user_name": username,
        "user_id": target_user_id
    })

# ================================
# 16. 管理员界面
# ================================
ADMIN_USER_ID = 1  # 可以改成实际管理员 id
@csrf_exempt
def admin_profile(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 403)
    elif user_id != ADMIN_USER_ID:
        return json_cn({"error": "不是管理员账号"}, 403)
    
    # --------------------------
    # 2. 返回管理员信息
    # --------------------------
    return json_cn({
        "message": "管理员界面",
        "user_id": user_id,
        "is_admin": True,
        "available_actions": [
            "admin_add_singer",
            "admin_delete_singer",
            "admin_add_album",
            "admin_delete_album",
            "admin_add_song",
            "admin_delete_song"
        ]
    })