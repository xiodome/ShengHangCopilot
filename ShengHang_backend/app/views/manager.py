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

    with connection.cursor() as cursor:
        cursor.execute(sql, [
            singer_name, singer_type, country, birthday, introduction
            ])

    return json_cn({"message": f"成功添加歌手：{singer_name}"})



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
    with connection.cursor() as cursor:
        cursor.execute(delete_sql, [singer_id])

    return json_cn({
        "message": "歌手删除成功",
        "singer_id": singer_id,
        "singer_name": singer_name
    })



# ================================
# 3. 新增专辑
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

    with connection.cursor() as cursor:
        cursor.execute(sql, [
            album_title, singer_id, release_date, cover_url, description,
            ])

    return json_cn({
        "message": "专辑已添加",
        "album_title": album_title,
        "singer_name": singer_name
    })



# ================================
# 4. 删除专辑
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

    with connection.cursor() as cursor:
        cursor.execute(sql, [album_id])

    return json_cn({
        "message": "专辑已删除",
        "album_id": album_id,
        "album_title": album_title
    })



# ================================
# 5. 添加歌曲
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
    return json_cn({
        "message": "歌曲已添加",
        "song_title": song_title,
        "song_id": song_id,
        "singers_id": singers_str
    })



# ================================
# 6. 删除歌曲
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
    # 先删除外键
    sql_delete_Song_Singer = "DELETE FROM Song_Singer WHERE song_id = %s"

    # 再删除本体
    sql_delete_Song = "DELETE FROM Song WHERE song_id=%s"

    with connection.cursor() as cursor:
        cursor.execute(sql_delete_Song_Singer, [song_id])
        cursor.execute(sql_delete_Song, [song_id])

    return json_cn({
        "message": "歌曲已删除",
        "song_title": song_title,
        "album_title": album_title,
        "singers": singers_str
    })



