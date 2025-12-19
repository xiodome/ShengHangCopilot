# 管理员管理模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from .tools import *


# ================================
# 1. 新增歌手
# ================================
@csrf_exempt
def admin_add_singer(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp
    
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取歌手数据并校验
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    if "singer_name" in data:
        singer_name = data.get("singer_name")
    else:
        return json_cn({"error": "未检测到歌手名称"}, 400)
    

    if "type" in data:
        singer_type = data.get("type")     
    else:
        return json_cn({"error": "错误歌手类别"}, 400)

    # -------- 可选字段，但要处理默认值 -------- 
    # 需要处理的所有可选字段
    optional_fields = ["country", "birthday", "introduction"]

    # 默认值
    defaults = {
        "country": None,
        "birthday": None,
        "introduction": None,
    }

    # 解析字段
    cleaned = {}
    for field in optional_fields:
        value = data.get(field, defaults[field])
        if value == "":
            value = defaults[field]
        cleaned[field] = value

    # 获得最终值
    country = cleaned["country"]
    birthday = cleaned["birthday"]
    introduction = cleaned["introduction"]


    # --------------------------
    # 3. 正式添加歌手
    # --------------------------
    sql = """
        INSERT 
        INTO Singer (singer_name, type, country, birthday, introduction)
        VALUES(%s, %s, %s, %s, %s)
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [
                singer_name, singer_type, country, birthday, introduction
                ])
            # 获取新 ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            new_singer_id = cursor.fetchone()[0]

        add_system_log(
            action=f"新增歌手: {singer_name}",
            target_table="Singer",
            target_id=new_singer_id,
            result="success"
        )

        return json_cn({"message": f"成功添加歌手：{singer_name}"})
    except Exception as e:
        add_system_log(
            action=f"新增歌手失败: {singer_name}",
            target_table="Singer",
            target_id=None,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)



# ================================
# 2. 删除歌手（管理员权限）
# ================================
@csrf_exempt
def admin_delete_singer(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取歌手id并校验
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST   


    if "singer_id" in data:
        singer_id = data.get("singer_id")
    else:
        return json_cn({"error": "未检测到歌手id"}, 400)
    
    if "singer_name" in data:
        singer_name = data.get("singer_name")
    else:
        return json_cn({"error": "未检测到歌手名字"}, 400)
    
    # --------------------------
    # 3. 检验歌手名字
    # --------------------------
    name_sql = """
        SELECT singer_name
        FROM Singer 
        WHERE singer_id = %s      
    """
    with connection.cursor() as cursor:
        cursor.execute(name_sql, [singer_id])
        row = cursor.fetchone()
    
    if row is None:
        return json_cn({"error": "歌手不存在"}, 404)
    elif singer_name != row[0]:
        return json_cn({"error": "歌手名与要删除的歌手不匹配"}, 400)

    # --------------------------
    # 4. 删除对应歌手
    # --------------------------

    delete_sql = """
        DELETE 
        FROM Singer 
        WHERE singer_id = %s   
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(delete_sql, [singer_id])

        add_system_log(
            action=f"删除歌手: {singer_name}",
            target_table="Singer",
            target_id=singer_id,
            result="success"
        )

        return json_cn({
            "message": "歌手删除成功",
            "singer_id": singer_id,
            "singer_name": singer_name
        })
    except Exception as e:
        add_system_log(
            action=f"删除歌手失败: {singer_name}",
            target_table="Singer",
            target_id=singer_id,
            result="fail"
        )

    return json_cn({"error": str(e)}, 500)



# ================================
# 3. 修改歌手信息（名称、类型、国籍、生日和简介）
# ================================
@csrf_exempt
def admin_update_singer(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 3. 校验 singer_id (必须存在)
    # --------------------------
    if "singer_id" in data:
        singer_id = data.get("singer_id")
    else:
        return json_cn({"error": "未检测到歌手id"}, 400)

    # 先检查数据库中是否有这个人
    check_sql = "SELECT singer_name FROM Singer WHERE singer_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(check_sql, [singer_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "该歌手不存在"}, 404)

    old_name = row[0]  # 用于返回提示

    # --------------------------
    # 4. 动态构建 UPDATE 语句
    # --------------------------
    # 定义允许修改的字段
    allowed_fields = ["singer_name", "type", "country", "birthday", "introduction"]

    update_clauses = []  # 存 "field = %s"
    params = []  # 存具体的值

    for field in allowed_fields:
        # 只有当前端传了这个字段时，才去更新它
        if field in data:
            value = data.get(field)

            # 特殊处理：如果前端传空字符串给可空的字段，视为将其设为 NULL
            if field in ["country", "birthday", "introduction"] and value == "":
                value = None

            update_clauses.append(f"{field} = %s")
            params.append(value)

    # 如果没有任何字段需要更新
    if not update_clauses:
        return json_cn({"error": "未检测到任何需要修改的字段"}, 400)

    # 拼接 SQL: UPDATE Singer SET field1=%s, field2=%s WHERE singer_id=%s
    sql = f"UPDATE Singer SET {', '.join(update_clauses)} WHERE singer_id = %s"

    # 把 ID 加到参数列表的最后，对应 WHERE 子句
    params.append(singer_id)

    # --------------------------
    # 5. 执行更新
    # --------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)

        add_system_log(
            action=f"成功修改歌手信息: {old_name}",
            target_table="Singer",
            target_id=singer_id,
            result="success"
        )

        return json_cn({
            "message": "歌手信息修改成功",
            "singer_id": singer_id,
            "original_name": old_name,
            "updated_fields": [k for k in data.keys() if k in allowed_fields]
        })

    except Exception as e:
        add_system_log(
            action=f"修改歌手信息失败: {old_name}",
            target_table="Singer",
            target_id=singer_id,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)
    


# ================================
# 4. 新增专辑
# ================================
@csrf_exempt
def admin_add_album(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 2. 获取专辑数据并校验
    # --------------------------
    if "album_title" in data:
        album_title = data.get("album_title")
    else:
        return json_cn({"error": "未检测到专辑名称"}, 400)
    
    if "singer_id" in data:
        singer_id = data.get("singer_id")
    else:
        return json_cn({"error": "未检测到歌手id"}, 400)
    
    sql_singer = """
        SELECT singer_name FROM Singer WHERE singer_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_singer, [singer_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌手不存在"}, 404)
    else: 
        singer_name = row[0]


    # -------- 可选字段，但要处理默认值 -------- 
    # 需要处理的所有可选字段
    optional_fields = ["release_date", "cover_url", "description"]

    # 默认值
    defaults = {
        "release_date": "1970-01-01",
        "cover_url": "/images/default_album_cover.jpg",
        "description": None,
    }

    # 解析字段
    cleaned = {}
    for field in optional_fields:
        value = data.get(field, defaults[field])
        if value == "":
            value = defaults[field]
        cleaned[field] = value

    # 获得最终值
    release_date = cleaned["release_date"]
    cover_url = cleaned["cover_url"]
    description = cleaned["description"]


    # --------------------------
    # 3. 正式添加专辑
    # --------------------------

    sql = """
        INSERT INTO Album (album_title, singer_id, release_date, cover_url, description)
        VALUES (%s, %s, %s, %s, %s)
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [
                album_title, singer_id, release_date, cover_url, description,
                ])
            # 获取新 ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            new_album_id = cursor.fetchone()[0]

        add_system_log(
            action=f"新增专辑: {album_title}",
            target_table="Album",
            target_id=new_album_id,
            result="success"
        )

        return json_cn({
            "message": "专辑已添加",
            "album_title": album_title,
            "singer_name": singer_name
        })

    except Exception as e:
        add_system_log(
            action=f"添加专辑失败: {album_title}",
            target_table="Album",
            target_id=None,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)



# ================================
# 5. 删除专辑
# ================================
@csrf_exempt
def admin_delete_album(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST


    # --------------------------
    # 2. 获取要删除的专辑数据
    # --------------------------
    if "album_id" in data:
        album_id = data.get("album_id")
    else:
        return json_cn({"error": "未检测到专辑id"}, 400)

    # --------------------------
    # 3. 获取专辑标题
    # --------------------------
    name_sql = """
        SELECT album_title
        FROM Album 
        WHERE album_id = %s      
    """
    with connection.cursor() as cursor:
        cursor.execute(name_sql, [album_id])
        row = cursor.fetchone()
    
    if row is None:
        return json_cn({"error": "专辑不存在"}, 404)
    
    album_title = row[0]

    # --------------------------
    # 4. 正式删除专辑
    # --------------------------
    sql = "DELETE FROM Album WHERE album_id = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [album_id])

        add_system_log(
            action=f"删除专辑: {album_title}",
            target_table="Album",
            target_id=album_id,
            result="success"
        )

        return json_cn({
            "message": "专辑已删除",
            "album_id": album_id,
            "album_title": album_title
        })

    except Exception as e:
        add_system_log(
            action=f"删除专辑失败: {album_title}",
            target_table="Album",
            target_id=album_id,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)



# ================================
# 6. 修改专辑信息（名称、歌手、发行日期、url地址和解释信息）
# ================================
@csrf_exempt
def admin_update_album(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 3. 校验 album_id (必须存在)
    # --------------------------
    if "album_id" in data:
        album_id = data.get("album_id")
    else:
        return json_cn({"error": "未检测到专辑id"}, 400)

    # 先检查数据库中是否有这张专辑
    check_sql = "SELECT album_title FROM Album WHERE album_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(check_sql, [album_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "该专辑不存在"}, 404)

    old_title = row[0]  # 用于返回提示

    # --------------------------
    # 4. 动态构建 UPDATE 语句
    # --------------------------
    # 定义允许修改的字段
    allowed_fields = ["album_title", "singer_id", "release_date", "cover_url", "description"]

    update_clauses = []  # 存 "field = %s"
    params = []  # 存具体的值

    for field in allowed_fields:
        # 只有当前端传了这个字段时，才去更新它
        if field in data:
            value = data.get(field)

            # 特殊处理：如果前端传空字符串给可空的字段，视为将其设为 NULL
            if field in ["description"] and value == "":
                value = None

            # 特殊处理：如果前端传空字符串给不可空但是有默认值的字段，视为设为默认值
            if field in ["release_date", "cover_url"] and value == "":
                if field == "release_date":
                    value = '1970-01-01'
                elif field == "cover_url":
                    value = '/images/default_album_cover.jpg'

            # 特殊判断：外键一定要存在
            if field in ["singer_id"]:
                check_singer_sql = "SELECT singer_name FROM Singer WHERE singer_id = %s"
                with connection.cursor() as cursor:
                    cursor.execute(check_singer_sql, [value])
                    row = cursor.fetchone()

                if not row:
                    return json_cn({"error": "修改信息中的歌手不存在"}, 404)

            update_clauses.append(f"{field} = %s")
            params.append(value)

    # 如果没有任何字段需要更新
    if not update_clauses:
        return json_cn({"error": "未检测到任何需要修改的字段"}, 400)

    # 拼接 SQL: UPDATE Album SET field1=%s, field2=%s WHERE album_id=%s
    sql = f"UPDATE Album SET {', '.join(update_clauses)} WHERE album_id = %s"

    # 把 ID 加到参数列表的最后，对应 WHERE 子句
    params.append(album_id)

    # --------------------------
    # 5. 执行更新
    # --------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)

        add_system_log(
            action=f"成功修改专辑信息: {old_title}",
            target_table="Album",
            target_id=album_id,
            result="success"
        )

        return json_cn({
            "message": "专辑信息修改成功",
            "album_id": album_id,
            "original_name": old_title,
            "updated_fields": [k for k in data.keys() if k in allowed_fields]
        })
    except Exception as e:
        add_system_log(
            action=f"修改专辑信息失败: {old_title}",
            target_table="Album",
            target_id=album_id,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)
    


# ================================
# 7. 添加歌曲
# ================================
@csrf_exempt
def admin_add_song(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST


    # --------------------------
    # 2. 获取歌曲数据并校验
    # --------------------------
    if "song_title" in data:
        song_title = data.get("song_title")
    else:
        return json_cn({"error": "未检测到歌曲名称"}, 400)
    
    if "album_id" in data:
        album_id = data.get("album_id")
    else:
        return json_cn({"error": "未检测到所属专辑id"}, 400)
    
    if "duration" in data:
        try:
            # 支持 mm:ss 或 m:ss
            minutes, seconds = map(int, data.get("duration").strip().split(":"))
            duration_seconds = minutes * 60 + seconds
        except Exception:
            return json_cn({"error": "歌曲时长格式错误，应为 mm:ss"}, 400)
    else:
        return json_cn({"error": "未检测到歌曲时长"}, 400)
    
    if "file_url" in data:
        file_url = data.get("file_url")
    else:
        return json_cn({"error": "未检测到歌曲文件路径"}, 400)


    # --------------------------
    # 3. 获取歌曲-歌手关系
    # --------------------------
    # 获取 singers_id
    if "singers_id" in data:
        singers_id = data.get("singers_id")
    else:
        return json_cn({"error": "未检测到歌曲的歌手id"}, 400)
    
    # 不是列表则自动改成单元素列表
    if not isinstance(singers_id, list):
        singers_id = [singers_id]


    # --------------------------
    # 4. 正式添加歌曲
    # --------------------------
    try:
        sql_insert_song = """
            INSERT INTO Song (song_title, album_id, duration, file_url)
            VALUES (%s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_insert_song, [
                song_title, album_id, duration_seconds, file_url
                ])

            # 获取新插入的 song_id
            cursor.execute("SELECT LAST_INSERT_ID()")
            song_id = cursor.fetchone()[0]


        # 插入多对多关系
        sql_insert_m2m = """
            INSERT INTO Song_Singer (song_id, singer_id)
            VALUES (%s, %s)
        """

        with connection.cursor() as cursor:
            for singer_id in singers_id:
                cursor.execute(sql_insert_m2m, [song_id, singer_id])

        singers_str = ", ".join(str(sid) for sid in singers_id)

        add_system_log(
            action=f"新增歌曲: {song_title}",
            target_table="Song",
            target_id=song_id,
            result="success"
        )

        return json_cn({
            "message": "歌曲已添加",
            "song_title": song_title,
            "song_id": song_id,
            "singers_id": singers_str
        })

    except Exception as e:
        add_system_log(
            action=f"添加歌曲失败: {song_title}",
            target_table="Song",
            target_id=None,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)



# ================================
# 8. 删除歌曲
# ================================
@csrf_exempt
def admin_delete_song(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    if "song_id" not in data:
        return json_cn({"error": "未检测到要删除的歌曲id"}, 400)
    else:
        song_id = data.get("song_id")


    # --------------------------
    # 2. 获取歌曲名、所属专辑和歌手
    # --------------------------
    sql_song = """
        SELECT s.song_title, a.album_title
        FROM Song s
        JOIN Album a ON a.album_id = s.album_id
        WHERE s.song_id = %s
    """

    sql_singers = """
        SELECT si.singer_name
        FROM Singer si
        JOIN Song_Singer ss ON si.singer_id = ss.singer_id
        WHERE ss.song_id = %s
    """

    with connection.cursor() as cursor:

        # 查询歌曲 + 专辑
        cursor.execute(sql_song, [song_id])
        song_row = cursor.fetchone()

        if not song_row:
            return json_cn({"error": "要删除的歌曲不存在"}, 404)
        
        song_title, album_title = song_row

        # 查询歌手列表
        cursor.execute(sql_singers, [song_id])
        singer_rows = cursor.fetchall()
        singers = [row[0] for row in singer_rows]
        singers_str = ", ".join(str(sid) for sid in singers)



    # --------------------------
    # 3. 正式删除歌曲
    # --------------------------
    try:
        # 先删除外键
        sql_delete_Song_Singer = "DELETE FROM Song_Singer WHERE song_id = %s"

        # 再删除本体
        sql_delete_Song = "DELETE FROM Song WHERE song_id=%s"

        with connection.cursor() as cursor:
            cursor.execute(sql_delete_Song_Singer, [song_id])
            cursor.execute(sql_delete_Song, [song_id])

        add_system_log(
            action=f"删除歌曲: {song_title}",
            target_table="Song",
            target_id=song_id,
            result="success"
        )

        return json_cn({
            "message": "歌曲已删除",
            "song_title": song_title,
            "album_title": album_title,
            "singers": singers_str
        })

    except Exception as e:
        add_system_log(
            action=f"添加歌曲失败: {song_title}",
            target_table="Song",
            target_id=song_id,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)



# ================================
# 9. 修改歌曲信息（歌曲名、专辑信息、持续时间、url地址和播放次数）
# ================================
@csrf_exempt
def admin_update_song(request):
    # --------------------------
    # 1. 检查管理员状态
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 3. 校验 song_id (必须存在)
    # --------------------------
    if "song_id" in data:
        song_id = data.get("song_id")
    else:
        return json_cn({"error": "未检测到歌曲id"}, 400)

    # 先检查数据库中是否有这首歌曲
    check_sql = "SELECT song_title FROM Song WHERE song_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(check_sql, [song_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "该歌曲不存在"}, 404)

    old_title = row[0]  # 用于返回提示

    # --------------------------
    # 4. 动态构建 UPDATE 语句
    # --------------------------
    # 定义允许修改的字段
    allowed_fields = ["song_title", "album_id", "duration", "file_url", "play_count"]

    update_clauses = []  # 存 "field = %s"
    params = []  # 存具体的值

    for field in allowed_fields:
        # 只有当前端传了这个字段时，才去更新它
        if field in data:
            value = data.get(field)

            # 特殊处理：如果前端传空字符串给不可空但是有默认值的字段，视为设为默认值
            if field in ["play_count"] and value == "":
                if field == "play_count":
                    value = 0

            # 特殊判断：外键一定要存在
            if field in ["album_id"]:
                check_album_sql = "SELECT album_title FROM Album WHERE album_id = %s"
                with connection.cursor() as cursor:
                    cursor.execute(check_album_sql, [value])
                    row = cursor.fetchone()

                if not row:
                    return json_cn({"error": "修改信息中的专辑不存在"}, 404)

            update_clauses.append(f"{field} = %s")
            params.append(value)

    # 如果没有任何字段需要更新
    if not update_clauses:
        return json_cn({"error": "未检测到任何需要修改的字段"}, 400)

    # 拼接 SQL: UPDATE Song SET field1=%s, field2=%s WHERE song_id=%s
    sql = f"UPDATE Song SET {', '.join(update_clauses)} WHERE song_id = %s"

    # 把 ID 加到参数列表的最后，对应 WHERE 子句
    params.append(song_id)

    # --------------------------
    # 5. 执行更新
    # --------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)

        add_system_log(
            action=f"修改歌曲信息成功: {old_title}",
            target_table="Song",
            target_id=song_id,
            result="success"
        )

        return json_cn({
            "message": "歌曲信息修改成功",
            "song_id": song_id,
            "original_name": old_title,
            "updated_fields": [k for k in data.keys() if k in allowed_fields]
        })

    except Exception as e:
        add_system_log(
            action=f"修改歌曲信息失败: {old_title}",
            target_table="Song",
            target_id=song_id,
            result="fail"
        )

        return json_cn({"error": str(e)}, 500)


# ================================
# 10. 查看系统日志
# ================================
@csrf_exempt
def get_system_logs(request):
    # --------------------------
    # 1. 权限检查
    # --------------------------
    ok, resp = require_admin(request)
    if not ok:
        return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取参数
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "JSON format error"}, 400)

    # 筛选条件
    filter_table = data.get("target_table")  # e.g., 'Singer'
    filter_result = data.get("result")  # e.g., 'fail'
    keyword = data.get("keyword")  # e.g., '删除'

    # 分页参数
    page = int(data.get("page", 1))
    page_size = int(data.get("page_size", 20))
    offset = (page - 1) * page_size

    # --------------------------
    # 3. 构建复用的 SQL 片段
    # --------------------------

    # base_sql: 存储 FROM 和 WHERE 部分，供 Count 和 Select 共用
    base_sql_parts = ["FROM SystemLog"]
    where_clauses = ["WHERE 1=1"]  # 使用 1=1 方便后续直接 append 'AND ...'
    base_params = []  # 存储筛选条件的参数

    # 3.1 拼接筛选条件
    if filter_table:
        where_clauses.append("AND target_table = %s")
        base_params.append(filter_table)

    if filter_result:
        where_clauses.append("AND result = %s")
        base_params.append(filter_result)

    if keyword:
        where_clauses.append("AND action LIKE %s")
        base_params.append(f"%{keyword}%")

    # 3.2 组合成完整的公共部分
    # 结果类似: "FROM SystemLog WHERE 1=1 AND target_table = %s AND action LIKE %s"
    common_sql_suffix = f"{base_sql_parts[0]} {' '.join(where_clauses)}"

    # --------------------------
    # 4. 执行数据库查询
    # --------------------------
    with connection.cursor() as cursor:

        # ====================
        # 第一查：统计总数 (Count)
        # ====================
        # 拼接: SELECT COUNT(*) + 公共后缀
        sql_count = f"SELECT COUNT(*) {common_sql_suffix}"

        cursor.execute(sql_count, base_params)  # 直接使用 base_params
        total_count = cursor.fetchone()[0]

        # ====================
        # 第二查：获取数据 (Select)
        # ====================
        # 拼接: SELECT 字段... + 公共后缀 + ORDER BY + LIMIT
        sql_data = f"""
            SELECT log_id, action, target_table, target_id, action_time, result
            {common_sql_suffix}
            ORDER BY action_time DESC
            LIMIT %s OFFSET %s
        """

        # 构造 Select 专用的参数列表：筛选参数 + 分页参数
        # 注意：这里必须是 base_params + [...]，顺序不能乱
        data_params = base_params + [page_size, offset]

        cursor.execute(sql_data, data_params)
        logs = dictfetchall(cursor)

    # --------------------------
    # 5. 返回结果
    # --------------------------
    return json_cn({
        "data": logs,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    })


# -------------------------------------------------
# 11. 获取用户行为统计 (管理员)
# 功能：
# 1. 统计指定时间段内的总数 (新增用户、播放、评论、收藏、建歌单)
# 2. 获取每日趋势图数据 (按天分组统计)
# 3. 获取最活跃用户排行 (按播放量排序)
# -------------------------------------------------
@csrf_exempt
def get_user_behavior_stats(request):
    # 1. 权限检查
    ok, resp = require_admin(request)
    if not ok: return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "JSON format error"}, 400)

    # 2. 获取时间范围参数
    # 默认查看最近 7 天
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    start_date = data.get("start_date", str(seven_days_ago))  # 'YYYY-MM-DD'
    end_date = data.get("end_date", str(today))

    # 构造 SQL 用的时间范围 (加上时间后缀以覆盖全天)
    start_dt = f"{start_date} 00:00:00"
    end_dt = f"{end_date} 23:59:59"

    stats_data = {}

    with connection.cursor() as cursor:

        # -------------------------------------------------
        # Part A: 数据概览 (Dashboard Summary)
        # 统计该时间段内的总量
        # -------------------------------------------------
        sql_summary = """
                      SELECT (SELECT COUNT(*) FROM User WHERE register_time BETWEEN %s AND %s)     as new_users, \
                             (SELECT COUNT(*) FROM PlayHistory WHERE play_time BETWEEN %s AND %s)  as total_plays, \
                             (SELECT COUNT(*) FROM Comment WHERE comment_time BETWEEN %s AND %s)   as total_comments, \
                             (SELECT COUNT(*) FROM Favorite WHERE favorite_time BETWEEN %s AND %s) as total_favorites, \
                             (SELECT COUNT(*) FROM Songlist WHERE create_time BETWEEN %s AND %s)   as new_songlists \
                      """
        # 参数需要重复填入，因为有5个子查询，每个都需要 start_dt, end_dt
        params_summary = [start_dt, end_dt] * 5

        cursor.execute(sql_summary, params_summary)
        summary_row = dictfetchall(cursor)[0]
        stats_data['summary'] = summary_row

        # -------------------------------------------------
        # Part B: 每日趋势 (Daily Trend)
        # 用于前端画折线图: x轴是日期, y轴是数量
        # -------------------------------------------------

        # 1. 每日播放量
        sql_trend_play = """
                         SELECT DATE_FORMAT(play_time, '%%Y-%%m-%%d') as date_str, COUNT(*) as count
                         FROM PlayHistory
                         WHERE play_time BETWEEN %s AND %s
                         GROUP BY date_str \
                         ORDER BY date_str \
                         """
        cursor.execute(sql_trend_play, [start_dt, end_dt])
        trend_play = dictfetchall(cursor)

        # 2. 每日新增用户
        sql_trend_user = """
                         SELECT DATE_FORMAT(register_time, '%%Y-%%m-%%d') as date_str, COUNT(*) as count
                         FROM User
                         WHERE register_time BETWEEN %s AND %s
                         GROUP BY date_str \
                         ORDER BY date_str \
                         """
        cursor.execute(sql_trend_user, [start_dt, end_dt])
        trend_user = dictfetchall(cursor)

        # 3. 每日互动 (评论+收藏)
        # 这里演示如何将两个表的统计合并 (Union All 然后 Sum)
        sql_trend_interaction = """
                                SELECT date_str, SUM(cnt) as count \
                                FROM (SELECT DATE_FORMAT(comment_time, '%%Y-%%m-%%d') as date_str, COUNT(*) as cnt \
                                      FROM Comment \
                                      WHERE comment_time BETWEEN %s AND %s \
                                      GROUP BY date_str \
                                      UNION ALL \
                                      SELECT DATE_FORMAT(favorite_time, '%%Y-%%m-%%d') as date_str, COUNT(*) as cnt \
                                      FROM Favorite \
                                      WHERE favorite_time BETWEEN %s AND %s \
                                      GROUP BY date_str) as temp_table
                                GROUP BY date_str \
                                ORDER BY date_str \
                                """
        cursor.execute(sql_trend_interaction, [start_dt, end_dt, start_dt, end_dt])
        trend_interaction = dictfetchall(cursor)

        stats_data['trends'] = {
            "plays": trend_play,
            "new_users": trend_user,
            "interactions": trend_interaction
        }

        # -------------------------------------------------
        # Part C: 活跃用户排行 (Top Active Users)
        # 找出这段时间内听歌最多的前10名用户
        # -------------------------------------------------
        sql_top_users = """
                        SELECT u.user_id, u.user_name, u.email, COUNT(ph.play_id) as play_count
                        FROM PlayHistory ph
                                 JOIN User u ON ph.user_id = u.user_id
                        WHERE ph.play_time BETWEEN %s AND %s
                        GROUP BY u.user_id, u.user_name, u.email
                        ORDER BY play_count DESC
                        LIMIT 10 \
                        """
        cursor.execute(sql_top_users, [start_dt, end_dt])
        top_users = dictfetchall(cursor)

        stats_data['top_active_users'] = top_users



    return json_cn(stats_data)



# ============================================================
# 12. 获取特定用户的详细行为统计 (用户画像)
# 功能：
# 1. 基础概览：听歌时长、评论数、收藏数、被关注数
# 2. 听歌偏好：最常听的歌手、最常听的风格(基于歌手类型)
# 3. 活跃趋势：该用户这段时间的每日听歌量
# ============================================================
@csrf_exempt
def get_specific_user_stats(request):
    # 1. 权限检查 (管理员可以看任何人，或者用户看自己)
    # 这里假设是管理员接口
    ok, resp = require_admin(request)
    if not ok: return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        return json_cn({"error": "JSON format error"}, 400)

    # 2. 获取参数
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return json_cn({"error": "未指定目标用户ID (target_user_id)"}, 400)

    # 时间范围 (默认最近 30 天)
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    start_date = data.get("start_date", str(thirty_days_ago))
    end_date = data.get("end_date", str(today))

    start_dt = f"{start_date} 00:00:00"
    end_dt = f"{end_date} 23:59:59"

    stats = {}

    with connection.cursor() as cursor:

        # -------------------------------------------------
        # Part 0: 用户基本信息确认
        # -------------------------------------------------
        sql_user_info = "SELECT user_name, email, register_time, status FROM User WHERE user_id = %s"
        cursor.execute(sql_user_info, [target_user_id])
        user_info = dictfetchall(cursor)
        if not user_info:
            return json_cn({"error": "用户不存在"}, 404)
        stats['user_info'] = user_info[0]

        # -------------------------------------------------
        # Part A: 行为概览 (Summary)
        # 统计该时间段内的各项核心指标
        # -------------------------------------------------
        # 使用 COALESCE 确保 SUM 返回 0 而不是 None
        sql_summary = """
                      SELECT (SELECT COUNT(*) \
                              FROM PlayHistory \
                              WHERE user_id = %s AND play_time BETWEEN %s AND %s)                                   as play_count, \
                             (SELECT COALESCE(SUM(play_duration), 0) \
                              FROM PlayHistory \
                              WHERE user_id = %s \
                                AND play_time BETWEEN %s AND %s)                                                    as total_duration_sec, \
                             (SELECT COUNT(*) \
                              FROM Comment \
                              WHERE user_id = %s \
                                AND comment_time BETWEEN %s AND %s)                                                 as comment_count, \
                             (SELECT COUNT(*) \
                              FROM Favorite \
                              WHERE user_id = %s \
                                AND favorite_time BETWEEN %s AND %s)                                                as favorite_count, \
                             (SELECT COUNT(*) \
                              FROM Songlist \
                              WHERE user_id = %s \
                                AND create_time BETWEEN %s AND %s)                                                  as songlist_created \
                      """
        # 参数顺序对应 SQL 中的 %s
        params_summary = [
            target_user_id, start_dt, end_dt,  # Play Count
            target_user_id, start_dt, end_dt,  # Duration
            target_user_id, start_dt, end_dt,  # Comment
            target_user_id, start_dt, end_dt,  # Favorite
            target_user_id, start_dt, end_dt  # Songlist
        ]

        cursor.execute(sql_summary, params_summary)
        stats['behavior_summary'] = dictfetchall(cursor)[0]

        # 转换一下时长显示 (分钟)
        total_sec = stats['behavior_summary']['total_duration_sec']
        stats['behavior_summary']['total_duration_min'] = round(total_sec / 60, 1)

        # -------------------------------------------------
        # Part B: 听歌偏好 (Preferences)
        # -------------------------------------------------

        # 1. 最常听的歌手 (Top Artist)
        # 关联路径: PlayHistory -> Song -> Song_Singer -> Singer
        sql_top_singer = """
                         SELECT s.singer_name, s.type, COUNT(*) as listen_count
                         FROM PlayHistory ph
                                  JOIN Song_Singer ss ON ph.song_id = ss.song_id
                                  JOIN Singer s ON ss.singer_id = s.singer_id
                         WHERE ph.user_id = %s \
                           AND ph.play_time BETWEEN %s AND %s
                         GROUP BY s.singer_id, s.singer_name, s.type
                         ORDER BY listen_count DESC
                         LIMIT 1 \
                         """
        cursor.execute(sql_top_singer, [target_user_id, start_dt, end_dt])
        top_singer_data = dictfetchall(cursor)
        stats['top_artist'] = top_singer_data[0] if top_singer_data else None

        # 2. 听歌时间分布 (比如：深夜党还是白日党)
        # 统计播放发生在哪个小时段 (0-23)
        sql_active_hour = """
                          SELECT HOUR(play_time) as hour_of_day, COUNT(*) as count
                          FROM PlayHistory
                          WHERE user_id = %s \
                            AND play_time BETWEEN %s AND %s
                          GROUP BY hour_of_day
                          ORDER BY count DESC
                          LIMIT 1 \
                          """
        cursor.execute(sql_active_hour, [target_user_id, start_dt, end_dt])
        hour_data = dictfetchall(cursor)
        stats['peak_hour'] = hour_data[0]['hour_of_day'] if hour_data else None

        # -------------------------------------------------
        # Part C: 每日活跃趋势 (Activity Trend)
        # 用于生成该用户的活跃度折线图
        # -------------------------------------------------
        sql_trend = """
                    SELECT DATE_FORMAT(play_time, '%%Y-%%m-%%d') as date_str,
                           COUNT(*)                              as plays,
                           SUM(play_duration)                    as duration
                    FROM PlayHistory
                    WHERE user_id = %s \
                      AND play_time BETWEEN %s AND %s
                    GROUP BY date_str
                    ORDER BY date_str ASC \
                    """
        cursor.execute(sql_trend, [target_user_id, start_dt, end_dt])
        stats['daily_trend'] = dictfetchall(cursor)

        # -------------------------------------------------
        # Part D: 社交影响力 (Social)
        # 统计粉丝数和关注数 (截止到目前，不限时间段，因为这是累积数据)
        # -------------------------------------------------
        sql_social = """
                     SELECT (SELECT COUNT(*) FROM UserFollow WHERE follower_id = %s) as following_count, \
                            (SELECT COUNT(*) FROM UserFollow WHERE followed_id = %s) as followers_count \
                     """
        cursor.execute(sql_social, [target_user_id, target_user_id])
        stats['social_stats'] = dictfetchall(cursor)[0]

    return json_cn(stats)

# ================================
# 13. 获取待审核评论列表
# ================================
@csrf_exempt
def admin_get_pending_comments(request):
    ok, resp = require_admin(request)
    if not ok: return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)
    page = data.get("page", 1)
    page_size = data.get("page_size", 20)
    offset = (page - 1) * page_size

    # 查询条件：状态是 '审核中' 或 '举报中'
    sql = """
          SELECT c.comment_id, \
                 c.content, \
                 c.status, \
                 c.comment_time, \
                 c.target_type, \
                 c.target_id,
                 u.user_id, \
                 u.user_name, \
                 u.status as user_status
          FROM Comment c
                   JOIN User u ON c.user_id = u.user_id
          WHERE c.status IN ('审核中', '举报中')
          ORDER BY c.comment_time DESC
          LIMIT %s OFFSET %s \
          """

    # 统计总数
    sql_count = "SELECT COUNT(*) FROM Comment WHERE status IN ('审核中', '举报中')"

    with connection.cursor() as cursor:
        cursor.execute(sql, [page_size, offset])
        comments = dictfetchall(cursor)

        cursor.execute(sql_count)
        total = cursor.fetchone()[0]

    return json_cn({
        "pending_comments": comments,
        "total": total,
        "page": page
    })

# ================================
# 14. 管理员审核评论
# ================================
@csrf_exempt
def admin_audit_comment(request):
    # 1. 权限检查
    ok, resp = require_admin(request)
    if not ok: return resp

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)
    comment_id = data.get("comment_id")
    audit_result = data.get("result")  # 'pass' (通过), 'reject' (驳回/删除)
    ban_user = data.get("ban_user", False)  # True (同时封禁用户)

    if not comment_id or audit_result not in ['pass', 'reject']:
        return json_cn({"error": "参数错误"}, 400)

    try:
        with connection.cursor() as cursor:

            # 先查一下评论信息 (为了获取 user_id 用于封禁)
            cursor.execute("SELECT user_id, content FROM Comment WHERE comment_id = %s", [comment_id])
            row = cursor.fetchone()
            if not row:
                return json_cn({"error": "评论不存在"}, 404)

            user_id, content_preview = row

            # ==============================
            # 情况 A: 审核通过 (改为正常)
            # ==============================
            if audit_result == 'pass':
                sql_pass = "UPDATE Comment SET status = '正常' WHERE comment_id = %s"
                cursor.execute(sql_pass, [comment_id])

                add_system_log(f"审核通过评论: {content_preview[:10]}...", "Comment", comment_id, "success")
                return json_cn({"message": "操作成功，评论已恢复正常"})

            # ==============================
            # 情况 B: 审核驳回 (删除评论)
            # ==============================
            elif audit_result == 'reject':

                # 1. 如果需要封禁用户
                if ban_user:
                    # 更新用户状态
                    sql_ban = "UPDATE User SET status = '封禁中' WHERE user_id = %s"
                    cursor.execute(sql_ban, [user_id])

                    # 这里只处理当前这一条评论。

                    add_system_log(f"封禁用户(因违规评论): ID={user_id}", "User", user_id, "success")

                # 2. 删除该条违规评论
                # 建议：如果只是"删除"，物理删除即可。
                # 如果想留存证据，可以把 status 改为 '已删除'
                # 这里直接删除
                sql_delete = "DELETE FROM Comment WHERE comment_id = %s"
                cursor.execute(sql_delete, [comment_id])

                action_msg = "审核驳回并删除" + ("(且封号)" if ban_user else "")
                add_system_log(f"{action_msg}: {content_preview[:10]}...", "Comment", comment_id, "success")

                return json_cn({"message": "违规评论已删除" + ("，用户已封禁" if ban_user else "")})

            return None

    except Exception as e:
        print(e)
        add_system_log(f"审核操作失败 ID={comment_id}", "Comment", comment_id, "fail")
        return json_cn({"error": "操作失败"}, 500)