# 收藏与歌单模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from .tools import *


# ================================
# 1. 歌单中心
# ================================
@csrf_exempt
def list_songlists(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再查看歌单"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 解析筛选参数
    # --------------------------
    is_public = request.GET.get("is_public")     # 可为 None / "1" / "0"
    sort_by = request.GET.get("sort_by", "create_time") # 默认按时间排序

    # --------------------------
    # 3. 构建 SQL
    # --------------------------
    sql = """
        SELECT songlist_id, songlist_title, description, create_time, cover_url, like_count, is_public
        FROM Songlist
        WHERE user_id = %s
    """

    params = [uid]

    # ---- 筛选公开性 ----
    if is_public in ["0", "1"]:
        sql += " AND is_public = %s"
        params.append(int(is_public))

    # ---- 排序 ----
    if sort_by == "likes":
        sql += " ORDER BY like_count DESC"
    else:
        sql += " ORDER BY create_time DESC"

    # --------------------------
    # 4. 执行 SQL 查询
    # --------------------------
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # --------------------------
    # 5. 返回 JSON
    # --------------------------
    songlists = []
    for r in rows:
        sid, title, desc, ctime, cover, likes, public = r
        songlists.append({
            "songlist_id": sid,
            "songlist_title": title,
            "description": desc,
            "create_time": ctime.strftime("%Y-%m-%d %H:%M") if ctime else None,
            "cover_url": cover,
            "like_count": likes,
            "is_public": bool(public)
        })

    return json_cn({
        "user_id": uid,
        "songlists": songlists,
        "total": len(songlists)
    })

# ================================
# 2. 创建歌单
# ================================
@csrf_exempt
def create_songlist(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再创建歌单"}, 403)
    
    uid = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 接收数据并校验
    # --------------------------
    # 允许 JSON + Form 两种格式
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # ----------- 必填字段 -----------
    if "songlist_title" in data:
        songlist_title = data.get("songlist_title").strip()
    else:
        return json_cn({"error": "缺少歌单名称"}, 400)

    # ----------- 可选字段 + 默认值处理 -----------
    optional_fields = ["description", "is_public", "cover_url"]
    defaults = {
        "description": None,
        "is_public": 1,
        "cover_url": "/images/default_songlist_cover.jpg"
    }

    cleaned = {}
    for field in optional_fields:
        value = data.get(field, defaults[field])
        if value == "":
            value = defaults[field]
        cleaned[field] = value

    description = cleaned["description"]
    is_public = int(cleaned["is_public"])
    cover_url = cleaned["cover_url"]

    # --------------------------
    # 3. 正式创建歌单
    # --------------------------
    sql = """
        INSERT INTO Songlist (user_id, songlist_title, description, is_public, cover_url)
        VALUES (%s, %s, %s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [uid, songlist_title, description, is_public, cover_url])

    return json_cn({
        "message": f"成功创建歌单：{songlist_title}"
    })


# ================================
# 3. 编辑歌单
# ================================
@csrf_exempt
def edit_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再编辑歌单"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title, description, is_public, cover_url
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌单不存在"}, 404)

    owner_id, old_title, old_desc, old_public, old_cover = row

    if owner_id != uid:
        return json_cn({"error": "无权限：你不是该歌单的创建者"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 3. POST：接收并校验数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # ----------- 必填字段 -----------
    if "songlist_title" in data:
        songlist_title = data.get("songlist_title").strip()
    else:
        return json_cn({"error": "修改失败：缺少歌单名称"}, 400)

    # ----------- 可选字段 -----------
    optional_fields = ["description", "is_public", "cover_url"]
    defaults = {
        "description": old_desc,
        "is_public": old_public,
        "cover_url": old_cover,
    }

    cleaned = {}
    for field in optional_fields:
        value = data.get(field, defaults[field])
        if value == "":
            value = defaults[field]
        cleaned[field] = value

    description = cleaned["description"]
    is_public = int(cleaned["is_public"])
    cover_url = cleaned["cover_url"]

    # --------------------------
    # 4. SQL 更新操作
    # --------------------------
    sql_update = """
        UPDATE Songlist
        SET songlist_title = %s, description = %s, is_public = %s, cover_url = %s
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_update, [
            songlist_title, description, is_public, cover_url, songlist_id
        ])

    return json_cn({
        "message": f"歌单修改成功：{songlist_title}",
        "songlist_id": songlist_id
    })


# ================================
# 4. 歌单详情
# ================================
@csrf_exempt
def songlist_profile(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行查看操作"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单信息
    # --------------------------
    sql_list = """
        SELECT user_id, songlist_title, description, create_time, cover_url,
               like_count, is_public
        FROM Songlist
        WHERE songlist_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌单不存在"}, 404)

    owner_id, title, desc, ctime, cover, likes, is_public = row

    # --------------------------
    # 3. 私密歌单权限判断
    # --------------------------
    is_owner = (uid == owner_id)
    if not is_owner and is_public == 0:
        return json_cn({"error": "这是一个私密歌单，你无权查看"}, 403)

    # --------------------------
    # 4. 查询歌单中的歌曲列表
    # --------------------------
    sql_songs = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            a.album_title AS album_title,
            sg.singer_id,
            sg.singer_name
        FROM Songlist_Song ss
        JOIN Song s ON ss.song_id = s.song_id
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss2 ON s.song_id = ss2.song_id
        JOIN Singer sg ON ss2.singer_id = sg.singer_id
        WHERE ss.songlist_id = %s
        ORDER BY ss.add_time DESC
    """

    sql_comment = """
        SELECT 
            u.user_id, u.user_name, c.comment_id, c.content, c.like_count, c.comment_time
        FROM Comment c 
        JOIN User u ON u.user_id = c.user_id
        WHERE target_id = %s AND target_type = 'songlist'
        ORDER BY comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [songlist_id])
        song_rows = cursor.fetchall()

        cursor.execute(sql_comment, [songlist_id])
        comment_rows = cursor.fetchall()

    # --------------------------
    # 5. 计算总时长
    # --------------------------
    total_duration = sum([row[2] for row in song_rows])

    # --------------------------
    # 6. 生成歌曲列表
    # --------------------------
    songs = []
    for (sid, stitle, dur, album_title, singer_id, singer_name) in song_rows:
        songs.append({
            "song_id": sid,
            "song_title": stitle,
            "duration": dur,
            "duration_formatted": format_time(dur),
            "album_title": album_title,
            "singer_id": singer_id,
            "singer_name": singer_name
        })


    # --------------------------
    # 7. 生成歌单评论列表
    # --------------------------
    comments = []
    for user_id, user_name, comment_id, content, like_count, comment_time in comment_rows:
        comments.append({
            "comment_id": comment_id,
            "user_id": user_id,
            "user_name": user_name,
            "content": content,
            "like_count": like_count,
            "comment_time": comment_time.strftime("%Y-%m-%d %H:%M") if comment_time else None
        })

    # --------------------------
    # 8. 返回歌单详情
    # --------------------------
    return json_cn({
        "songlist_id": songlist_id,
        "songlist_title": title,
        "description": desc,
        "create_time": ctime.strftime("%Y-%m-%d %H:%M") if ctime else None,
        "cover_url": cover,
        "like_count": likes,
        "is_public": bool(is_public),
        "is_owner": is_owner,
        "owner_id": owner_id,
        "song_count": len(songs),
        "total_duration": total_duration,
        "total_duration_formatted": format_time(total_duration),
        "songs": songs,
        "comment_count": len(comments),
        "comments": comments
    })




# ================================
# 5. 删除歌单
# ================================
@csrf_exempt
def delete_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行删除操作"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "删除失败：该歌单不存在"}, 404)

    owner_id, title = row

    if owner_id != uid:
        return json_cn({"error": "无权限删除：你不是该歌单的创建者"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 3. POST：执行删除
    # --------------------------
    sql_delete = """
        DELETE FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_delete, [songlist_id])

    return json_cn({
        "message": f"成功删除歌单：{title}",
        "songlist_id": songlist_id
    })



# ================================
# 6. 向歌单插入歌曲
# ================================
@csrf_exempt
def songlist_add_song(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再添加歌曲到歌单"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_select = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_select, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "该歌单不存在"}, 404)

    owner_id, songlist_title = row

    if owner_id != uid:
        return json_cn({"error": "无权限：你不是该歌单的创建者"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 3. POST：接收并校验数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    if "song_id" not in data:
        return json_cn({"error": "添加失败：缺少 song_id"}, 400)

    try:
        song_id = int(data.get("song_id"))
    except:
        return json_cn({"error": "song_id 必须是数字"}, 400)

    # --------------------------
    # 4. 检查歌曲是否存在
    # --------------------------
    sql_check_song = "SELECT song_id, song_title FROM Song WHERE song_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_check_song, [song_id])
        song_row = cursor.fetchone()

    if not song_row:
        return json_cn({"error": f"歌曲不存在：ID = {song_id}"}, 404)

    song_title = song_row[1]

    # --------------------------
    # 5. 检查是否已在歌单中
    # --------------------------
    sql_check_exist = """
        SELECT 1 FROM Songlist_Song
        WHERE songlist_id = %s AND song_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_check_exist, [songlist_id, song_id])
        exists = cursor.fetchone()

    if exists:
        return json_cn({"error": f"添加失败：歌曲《{song_title}》已在歌单中"}, 400)

    # --------------------------
    # 6. SQL 插入关系记录
    # --------------------------
    sql_insert = """
        INSERT INTO Songlist_Song (songlist_id, song_id)
        VALUES (%s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [songlist_id, song_id])

    return json_cn({
        "message": f"成功添加歌曲：{song_title}",
        "songlist_id": songlist_id,
        "song_id": song_id
    })



# ================================
# 7. 删除歌单中的歌曲
# ================================
@csrf_exempt
def songlist_delete_song(request, songlist_id, song_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行移除操作"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单是否存在 + 权限检查
    # --------------------------
    sql_songlist = """
        SELECT user_id, songlist_title
        FROM Songlist
        WHERE songlist_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songlist, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌单不存在"}, 404)

    owner_id, songlist_title = row

    if owner_id != uid:
        return json_cn({"error": "无权限：你不是该歌单的创建者"}, 403)

    # --------------------------
    # 3. 查询歌曲是否存在 + 是否在歌单中
    # --------------------------
    sql_song = "SELECT song_title FROM Song WHERE song_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql_song, [song_id])
        song_row = cursor.fetchone()

    if not song_row:
        return json_cn({"error": f"歌曲不存在：ID = {song_id}"}, 404)

    song_title = song_row[0]

    sql_check = """
        SELECT 1 FROM Songlist_Song
        WHERE songlist_id = %s AND song_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [songlist_id, song_id])
        exists = cursor.fetchone()

    if not exists:
        return json_cn({"error": f"歌曲《{song_title}》不在该歌单中"}, 400)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 4. POST：执行删除
    # --------------------------
    sql_delete = """
        DELETE FROM Songlist_Song
        WHERE songlist_id = %s AND song_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_delete, [songlist_id, song_id])

    return json_cn({
        "message": f"已成功从歌单移除：{song_title}",
        "songlist_id": songlist_id,
        "song_id": song_id
    })



# ================================
# 8. 对歌单中的歌曲排序
# ================================
@csrf_exempt
def sort_songlist(request, songlist_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行排序操作"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 查询歌单信息（获取权限）
    # --------------------------
    sql_info = """
        SELECT user_id, songlist_title, is_public
        FROM Songlist
        WHERE songlist_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_info, [songlist_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌单不存在"}, 404)

    owner_id, title, is_public = row

    # 私密歌单权限检查
    if is_public == 0 and uid != owner_id:
        return json_cn({"error": "无权查看私密歌单"}, 403)

    # --------------------------
    # 3. 获取排序方式（默认按添加时间）
    # --------------------------
    sort = request.GET.get("sort", "add_time")  # add_time / duration / play_count

    # 白名单，安全避免 SQL 注入
    sort_map = {
        "add_time": "ss.add_time DESC",
        "duration": "s.duration DESC",
        "play_count": "s.play_count DESC",
    }

    if sort not in sort_map:
        sort = "add_time"

    order_sql = sort_map[sort]

    # --------------------------
    # 4. 查询排序后的歌曲列表
    # --------------------------
    sql_songs = f"""
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            a.album_title AS album_title,
            sg.singer_id,
            sg.singer_name,
            ss.add_time
        FROM Songlist_Song ss
        JOIN Song s ON ss.song_id = s.song_id
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss2 ON s.song_id = ss2.song_id
        JOIN Singer sg ON ss2.singer_id = sg.singer_id
        WHERE ss.songlist_id = %s
        ORDER BY {order_sql}
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [songlist_id])
        rows = cursor.fetchall()

    # --------------------------
    # 5. 格式化返回数据
    # --------------------------
    songs = []
    for sid, name, duration, album, singer_id, singer_name, add_time in rows:
        songs.append({
            "song_id": sid,
            "song_title": name,
            "duration": duration,
            "duration_formatted": format_time(duration),
            "album_title": album,
            "singer_id": singer_id,
            "singer_name": singer_name,
            "add_time": add_time.strftime("%Y-%m-%d %H:%M") if add_time else None
        })

    # --------------------------
    # 6. 返回结果
    # --------------------------
    return json_cn({
        "songlist_id": songlist_id,
        "songlist_title": title,
        "sort_by": sort,
        "songs": songs,
        "total": len(songs)
    })



# ==========================
# 9. 搜索歌单
# ==========================
@csrf_exempt
def search_songlist(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        return json_cn({"error": "请先登录"}, 403)

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST    

        
    # --------------------------
    # 2. 获取搜索标签
    # --------------------------
    songlist_title = data.get("songlist_title", "").strip()

    filters = []
    params = []

    if songlist_title:
        filters.append("sl.songlist_title LIKE %s")
        params.append(f"%{songlist_title}%")


    # --------------------------
    # 3. 查询歌单信息
    # --------------------------
    sql_songlist = """
        SELECT sl.songlist_id, sl.songlist_title, sl.cover_url, u.user_id, u.user_name
        FROM Songlist sl
        JOIN User u ON u.user_id = sl.user_id
    """

    if filters:
        sql_songlist += " WHERE " + " AND ".join(filters)


    with connection.cursor() as cursor:
        cursor.execute(sql_songlist, params)
        rows = cursor.fetchall()

        if not rows:
            return json_cn({"message": "未找到符合歌单", "songlists": []})
            
        # --------------------------
        # 4. 返回搜索结果
        # --------------------------
        songlists = []
        for (songlist_id, songlist_title, cover_url, user_id, user_name) in rows:
            songlists.append({
                "songlist_id": songlist_id,
                "songlist_title": songlist_title,
                "cover_url": cover_url,
                "user_id": user_id,
                "user_name": user_name
            })

    return json_cn({
        "total": len(songlists),
        "songlists": songlists
    })



# ================================
# 10.点赞歌单
# ================================
@csrf_exempt
def like_songlist(request, songlist_id):
        
    sql = """
        UPDATE Songlist
        SET like_count = like_count + 1
        WHERE Songlist_id = %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [songlist_id])

    return json_cn({
        "message": "点赞成功",
        "songlist_id": songlist_id
    })
    


# ==========================
# 11. 个人收藏
# ==========================
@csrf_exempt
def list_favorite(request):
    # --------------------------
    # 1. 必须登录
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再查看收藏"}, 403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 获取收藏的歌曲
    # --------------------------
    sql_song = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            f.favorite_time
        FROM Favorite f
        JOIN Song s ON f.target_id = s.song_id
        WHERE f.user_id = %s AND f.target_type = 'song'
        ORDER BY f.favorite_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [uid])
        songs = cursor.fetchall()

    song_count = len(songs)
    song_total_duration = sum([s[2] for s in songs]) if songs else 0


    # --------------------------
    # 3. 获取收藏的专辑
    # --------------------------
    sql_album = """
        SELECT 
            al.album_id,
            al.album_title,
            al.release_date,
            f.favorite_time
        FROM Favorite f
        JOIN Album al ON f.target_id = al.album_id
        WHERE f.user_id = %s AND f.target_type = 'album'
        ORDER BY f.favorite_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_album, [uid])
        albums = cursor.fetchall()

    album_count = len(albums)

    # --------------------------
    # 4. 获取收藏的歌单
    # --------------------------
    sql_songlist = """
        SELECT 
            sl.songlist_id,
            sl.songlist_title,
            f.favorite_time
        FROM Favorite f
        JOIN Songlist sl ON f.target_id = sl.songlist_id
        WHERE f.user_id = %s AND f.target_type = 'songlist'
        ORDER BY f.favorite_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songlist, [uid])
        songlists = cursor.fetchall()

    songlist_count = len(songlists)

    # --------------------------
    # 5. 格式化返回数据
    # --------------------------

    # ---------- 收藏歌曲 ----------
    favorite_songs = []
    for sid, title, duration, ctime in songs:
        favorite_songs.append({
            "song_id": sid,
            "song_title": title,
            "duration": duration,
            "duration_formatted": format_time(duration),
            "favorite_time": ctime.strftime("%Y-%m-%d %H:%M") if ctime else None
        })

    # ---------- 收藏专辑 ----------
    favorite_albums = []
    for aid, title, date, ctime in albums:
        favorite_albums.append({
            "album_id": aid,
            "album_title": title,
            "release_date": str(date) if date else None,
            "favorite_time": ctime.strftime("%Y-%m-%d %H:%M") if ctime else None
        })

    # ---------- 收藏歌单 ----------
    favorite_songlists = []
    for lid, title, ctime in songlists:
        favorite_songlists.append({
            "songlist_id": lid,
            "songlist_title": title,
            "favorite_time": ctime.strftime("%Y-%m-%d %H:%M") if ctime else None
        })

    # ---------- 返回 ----------
    return json_cn({
        "user_id": uid,
        "songs": {
            "count": song_count,
            "total_duration": song_total_duration,
            "total_duration_formatted": format_time(song_total_duration),
            "items": favorite_songs
        },
        "albums": {
            "count": album_count,
            "items": favorite_albums
        },
        "songlists": {
            "count": songlist_count,
            "items": favorite_songlists
        }
    })




# ================================
# 12. 进行收藏操作
# ================================
@csrf_exempt
def add_favorite(request):
    # --------------------------
    # 1. 必须登录
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再进行收藏"}, 403)

    uid = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    target_type = data.get("type")
    target_id = data.get("id")

    if target_type not in ["song", "album", "songlist"]:
        return json_cn({"error": "非法的收藏类型"}, 400)

    # --------------------------
    # 3. 检查是否已收藏
    # --------------------------
    sql_check = f"""
        SELECT 1
        FROM Favorite
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, target_type, target_id])
        exists = cursor.fetchone()

    if exists:
        return json_cn({"error": "已经收藏过了"}, 400)

    # --------------------------
    # 4. 插入收藏记录
    # --------------------------
    sql_insert = f"""
        INSERT INTO Favorite(user_id, target_type, target_id)
        VALUES(%s, %s, %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [uid, target_type, target_id])

    # --------------------------
    # 5. 返回成功
    # --------------------------
    return json_cn({
        "message": "收藏成功",
        "target_type": target_type,
        "target_id": target_id
    })



# ================================
# 13. 取消收藏
# ================================
@csrf_exempt
def delete_favorite(request):
    # --------------------------
    # 1. 检验登录
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录再进行操作"}, 403)

    uid = request.session["user_id"]

    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    target_type = data.get("type")
    target_id = data.get("id")

    if target_type not in ["song", "album", "songlist"]:
        return json_cn({"error": "非法的收藏类型"}, 400)

    # --------------------------
    # 3. 检查是否已收藏
    # --------------------------
    sql_check = f"""
        SELECT 1
        FROM Favorite
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, target_type, target_id])
        exists = cursor.fetchone()

    if not exists:
        return json_cn({"error": "未收藏不能取消"}, 400)

    # --------------------------
    # 4. 删除收藏记录
    # --------------------------
    sql_delete = f"""
        DELETE FROM Favorite
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_delete, [uid, target_type, target_id])

    # --------------------------
    # 5. 返回成功
    # --------------------------
    return json_cn({
        "message": "取消收藏成功",
        "target_type": target_type,
        "target_id": target_id
    })


# ================================
# 14. "我收藏的歌曲" 统计
# ================================
def get_my_favorite_songs_stats(request):
    """
    将用户收藏的歌曲视为一个"默认歌单"，返回列表和总时长
    """
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    current_user_id = request.session["user_id"]

    # 1. 计算收藏歌曲总时长
    sql_duration = """
        SELECT SUM(s.duration)
        FROM Favorite f
        JOIN Song s ON f.target_id = s.song_id
        WHERE f.user_id = %s
          AND f.target_type = 'song'
    """

    # 2. 获取歌曲列表
    sql_list = """
        SELECT s.song_id, s.song_title, s.duration, s.play_count, f.favorite_time
        FROM Favorite f
        JOIN Song s ON f.target_id = s.song_id
        WHERE f.user_id = %s
          AND f.target_type = 'song'
        ORDER BY f.favorite_time DESC
    """

    with connection.cursor() as cursor:
        # 总时长
        cursor.execute(sql_duration, [current_user_id])
        duration_row = cursor.fetchone()
        total_duration = duration_row[0] if duration_row and duration_row[0] else 0

        # 歌曲列表
        cursor.execute(sql_list, [current_user_id])
        songs = dictfetchall(cursor)

    return json_cn({
        "list_name": "我收藏的歌曲",
        "total_duration": total_duration,
        "total_duration_formatted": format_time(total_duration),
        "count": len(songs),
        "songs": songs
    })


# ================================
# 15. 平台收藏排行榜
# ================================
def get_platform_top_favorites(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # type: 'song', 'album', 'songlist'
    target_type = data.get("target_type", "song")
    limit = data.get("limit", 10)  # 默认取前10

    if target_type == 'song':
        sql = """
            SELECT f.target_id, COUNT(*) as fav_count, s.song_title as name
            FROM Favorite f
            JOIN Song s ON f.target_id = s.song_id
            WHERE f.target_type = 'song'
            GROUP BY f.target_id, s.song_title
            ORDER BY fav_count DESC
            LIMIT %s
        """
    elif target_type == 'album':
        sql = """
            SELECT f.target_id, COUNT(*) as fav_count, a.album_title as name
            FROM Favorite f
            JOIN Album a ON f.target_id = a.album_id
            WHERE f.target_type = 'album'
            GROUP BY f.target_id, a.album_title
            ORDER BY fav_count DESC
            LIMIT %s
        """
    elif target_type == 'songlist':
        sql = """
            SELECT f.target_id, COUNT(*) as fav_count, sl.songlist_title as name
            FROM Favorite f
            JOIN Songlist sl ON f.target_id = sl.songlist_id
            WHERE f.target_type = 'songlist'
            GROUP BY f.target_id, sl.songlist_title
            ORDER BY fav_count DESC
            LIMIT %s
        """
    else:
        return json_cn({"error": "类型错误"}, 400)

    with connection.cursor() as cursor:
        cursor.execute(sql, [limit])
        result = dictfetchall(cursor)

    return json_cn({"ranking": result, "type": target_type})

