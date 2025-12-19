# 歌手与音乐模块

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from .tools import *


# ================================
# 1. 音乐中心
# ================================
@csrf_exempt
def music(request):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行查看操作"}, 403)

    uid = request.session["user_id"]

    return json_cn({
        "message": "音乐中心",
        "user_id": uid,
        "available_actions": [
            "search_singer",
            "search_album", 
            "search_song",
            "search_songlist"
        ]
    })




# ================================
# 2. 搜索歌手
# ================================
@csrf_exempt
def search_singer(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录"}, 403)
    
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    # --------------------------
    # 2. 获取筛选标签
    # --------------------------
    filters = []
    params = []

    singer_type = data.get("type")
    country = data.get("country")
    singer_name = data.get("singer_name")

    if singer_type and singer_type != "":
        filters.append("type = %s")
        params.append(singer_type)
    if country and country != "":
        filters.append("country = %s")
        params.append(country)
    if singer_name and singer_name != "":
        filters.append("singer_name LIKE %s")
        params.append("%" + singer_name + "%")

    # --------------------------
    # 3. 正式查找歌手
    # --------------------------

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    sql = f"""
        SELECT singer_id, singer_name, type, country
        FROM Singer
        {where_clause}
        ORDER BY singer_name ASC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # ------------------------
    # 4. 查询数量
    # ------------------------
    sql_count = f"""
        SELECT COUNT(*)
        FROM Singer
        {where_clause}
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_count, params)
        total = cursor.fetchone()[0]


    # --------------------------
    # 5. 返回搜索结果
    # --------------------------
    singers = []
    for (singer_id, singer_name, singer_type, country) in rows:
        singers.append({
            "singer_id": singer_id,
            "singer_name": singer_name,
            "type": singer_type,
            "country": country
        })

    return json_cn({
        "total": total,
        "singers": singers
    })




# ================================
# 3. 歌手详情
# ================================
@csrf_exempt
def singer_profile(request, singer_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行查看操作"}, 403)

    # --------------------------
    # 2. 查询歌手信息
    # --------------------------
    sql_list = """
        SELECT singer_name, type, country, birthday, introduction
        FROM Singer
        WHERE singer_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [singer_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "歌手不存在"}, 404)

    singer_name, singer_type, country, birthday, introduction = row


    # --------------------------
    # 3. 查询歌手的歌曲列表
    # --------------------------
    sql_songs = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration,
            a.album_title
        FROM Song s
        JOIN Album a ON s.album_id = a.album_id
        JOIN Song_Singer ss ON s.song_id = ss.song_id
        WHERE ss.singer_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songs, [singer_id])
        song_rows = cursor.fetchall()

    # --------------------------
    # 4. 生成歌手歌曲列表
    # --------------------------
    songs = []
    for (song_id, song_title, duration, album_title) in song_rows:
        songs.append({
            "song_id": song_id,
            "song_title": song_title,
            "duration": duration,
            "duration_formatted": format_time(duration),
            "album_title": album_title
        })


    # --------------------------
    # 5. 查询歌手的专辑列表
    # --------------------------
    sql_albums = """
        SELECT 
            a.album_id,
            a.album_title,
            a.release_date
        FROM Album a
        JOIN Singer s ON s.singer_id = a.singer_id
        WHERE s.singer_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_albums, [singer_id])
        album_rows = cursor.fetchall()

    # --------------------------
    # 6. 生成歌手专辑列表
    # --------------------------
    albums = []
    for (album_id, album_title, release_date) in album_rows:
        albums.append({
            "album_id": album_id,
            "album_title": album_title,
            "release_date": str(release_date) if release_date else None
        })

    # --------------------------
    # 7. 返回歌手详情
    # --------------------------
    return json_cn({
        "singer_id": singer_id,
        "singer_name": singer_name,
        "type": singer_type,
        "country": country,
        "birthday": str(birthday) if birthday else None,
        "introduction": introduction,
        "song_count": len(songs),
        "songs": songs,
        "album_count": len(albums),
        "albums": albums
    })



# ================================
# 4. 搜索专辑
# ================================
@csrf_exempt
def search_album(request):
    # --------------------------
    # 1. 登录校验
    # --------------------------
    if "user_id" not in request.session:
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
    album_title = data.get("album_title", "").strip()
    singer_name = data.get("singer_name", "").strip()

    filters = []
    params = []

    if album_title:
        filters.append("a.album_title LIKE %s")
        params.append(f"%{album_title}%")
    if singer_name:
        filters.append("s.singer_name LIKE %s")
        params.append(f"%{singer_name}%")


    # --------------------------
    # 3. 查询专辑信息
    # --------------------------
    sql_album = """
        SELECT a.album_title, sg.singer_name, a.release_date, a.album_id
        FROM Album a
        JOIN Singer sg ON a.singer_id = sg.singer_id
    """

    if filters:
        sql_album += " WHERE " + " AND ".join(filters)

    sql_album += " GROUP BY a.album_id"

    with connection.cursor() as cursor:
        cursor.execute(sql_album, params)
        rows = cursor.fetchall()


    if not rows:
        return json_cn({"message": "未找到符合条件专辑", "albums": []})


    # --------------------------
    # 4. 返回搜索结果
    # --------------------------
    albums = []
    for (album_title, singer_name, release_date, album_id) in rows:
        albums.append({
            "album_id": album_id,
            "album_title": album_title,
            "singer_name": singer_name,
            "release_date": str(release_date) if release_date else None
        })

    return json_cn({
        "total": len(albums),
        "albums": albums
    })



# ================================
# 5. 专辑详情
# ================================
@csrf_exempt
def album_profile(request, album_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行查看操作"}, 403)

    # --------------------------
    # 2. 查询专辑信息
    # --------------------------
    sql_list = """
        SELECT album_title, release_date, cover_url, description, sg.singer_name, sg.singer_id
        FROM Album a
        JOIN Singer sg ON sg.singer_id = a.singer_id
        WHERE a.album_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_list, [album_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "专辑不存在"}, 404)

    album_title, release_date, cover_url, description, singer_name, singer_id = row


    # --------------------------
    # 3. 查询专辑的歌曲列表
    # --------------------------
    sql_albums = """
        SELECT 
            s.song_id,
            s.song_title,
            s.duration
        FROM Album a
        JOIN Song s ON s.album_id = a.album_id       
        WHERE a.album_id = %s
    """

    sql_total_duration = """
        SELECT 
            IFNULL(SUM(s.duration), 0) AS total_duration
        FROM Album a
        JOIN Song s ON s.album_id = a.album_id
        WHERE a.album_id = %s
    """

    sql_singers = """
        SELECT
            sg.singer_id,
            sg.singer_name
        FROM Singer sg
        JOIN Song_Singer ss ON ss.singer_id = sg.singer_id
        WHERE ss.song_id = %s
    """

    sql_comment = """
        SELECT 
            u.user_id, u.user_name, c.comment_id, c.content, c.like_count, c.comment_time
        FROM Comment c 
        JOIN User u ON u.user_id = c.user_id
        WHERE target_id = %s AND target_type = 'album'
        ORDER BY comment_time DESC
    """

    # --------------------------
    # 4. 查询并生成专辑歌曲列表
    # --------------------------
    songs = []

    with connection.cursor() as cursor:
        cursor.execute(sql_albums, [album_id])
        song_rows = cursor.fetchall()

        cursor.execute(sql_total_duration, [album_id])
        total_duration = cursor.fetchone()[0]
        
        for (song_id, song_title, duration) in song_rows:
            cursor.execute(sql_singers, [song_id])
            singer_rows = cursor.fetchall()
            song_singers = [{"singer_id": row[0], "singer_name": row[1]} for row in singer_rows]

            songs.append({
                "song_id": song_id,
                "song_title": song_title,
                "duration": duration,
                "duration_formatted": format_time(duration),
                "singers": song_singers
            })

        cursor.execute(sql_comment, [album_id])
        comment_rows = cursor.fetchall()


    # --------------------------
    # 5. 生成专辑评论列表
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
    # 6. 返回专辑详情
    # --------------------------
    return json_cn({
        "album_id": album_id,
        "album_title": album_title,
        "singer_id": singer_id,
        "singer_name": singer_name,
        "release_date": str(release_date) if release_date else None,
        "cover_url": cover_url,
        "description": description,
        "song_count": len(songs),
        "total_duration": total_duration,
        "total_duration_formatted": format_time(total_duration),
        "songs": songs,
        "comment_count": len(comments),
        "comments": comments
    })



# ================================
# 6. 搜索歌曲
# ================================
@csrf_exempt
def search_song(request):
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
    song_title = data.get("song_title", "").strip()
    album_title = data.get("album_title", "").strip()
    singer_name = data.get("singer_name", "").strip()

    filters = []
    params = []

    if song_title:
        filters.append("s.song_title LIKE %s")
        params.append(f"%{song_title}%")
    if album_title:
        filters.append("a.album_title LIKE %s")
        params.append(f"%{album_title}%")
    if singer_name:
        filters.append("si.singer_name LIKE %s")
        params.append(f"%{singer_name}%")


    # --------------------------
    # 3. 查询歌曲信息
    # --------------------------
    # Base SQL query
    sql_song = """
        SELECT DISTINCT s.song_id, s.song_title, s.duration, a.album_title
        FROM Song s
        JOIN Album a ON a.album_id = s.album_id
    """
    
    # Add JOIN for singer filter if needed
    if singer_name:
        sql_song += """
        JOIN Song_Singer ss ON s.song_id = ss.song_id
        JOIN Singer si ON ss.singer_id = si.singer_id
        """
    
    sql_singers = """
        SELECT si.singer_id, si.singer_name 
        FROM Singer si
        JOIN Song_Singer ss ON si.singer_id = ss.singer_id
        WHERE ss.song_id = %s
    """

    if filters:
        sql_song += " WHERE " + " AND ".join(filters)



    with connection.cursor() as cursor:
        cursor.execute(sql_song, params)
        rows = cursor.fetchall()

        if not rows:
            return json_cn({"message": "未找到符合歌曲", "songs": []})
            
        # --------------------------
        # 4. 生成歌曲列表
        # --------------------------
        songs = []
        for (song_id, song_title, duration, album_title) in rows:
            cursor.execute(sql_singers, [song_id])
            singer_rows = cursor.fetchall()
            song_singers = [{"singer_id": row[0], "singer_name": row[1]} for row in singer_rows]

            songs.append({
                "song_id": song_id,
                "song_title": song_title,
                "duration": duration,
                "duration_formatted": format_time(duration),
                "album_title": album_title,
                "singers": song_singers
            })

    return json_cn({
        "total": len(songs),
        "songs": songs
    })




# ================================
# 7. 歌曲详情
# ================================
@csrf_exempt
def song_profile(request, song_id):
    # --------------------------
    # 1. 检查登录状态
    # --------------------------
    if "user_id" not in request.session:
        return json_cn({"error": "请先登录后再进行查看操作"}, 403)

    # --------------------------
    # 2. 查询歌曲信息
    # --------------------------
    sql_song = """
        SELECT s.song_id, s.song_title, s.duration, a.album_id, a.album_title
        FROM Song s
        JOIN Album a ON a.album_id = s.album_id
        WHERE s.song_id = %s
    """

    sql_singer = """
        SELECT sg.singer_id, sg.singer_name
        FROM Singer sg
        JOIN Song_Singer ss ON ss.singer_id = sg.singer_id
        WHERE ss.song_id = %s
    """

    sql_comment = """
        SELECT 
            u.user_id, u.user_name, c.comment_id, c.content, c.like_count, c.comment_time
        FROM Comment c 
        JOIN User u ON u.user_id = c.user_id
        WHERE target_id = %s AND target_type = 'song'
        ORDER BY comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [song_id])
        song_row = cursor.fetchone()
        
        if not song_row:
            return json_cn({"error": "歌曲不存在"}, 404)
        
        song_id, song_title, duration, album_id, album_title = song_row

        cursor.execute(sql_singer, [song_id])
        singer_rows = cursor.fetchall()
        singers = [{"singer_id": row[0], "singer_name": row[1]} for row in singer_rows]

        cursor.execute(sql_comment, [song_id])
        comment_rows = cursor.fetchall()


    # --------------------------
    # 3. 生成歌曲评论列表
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
    # 4. 返回歌曲详情
    # --------------------------
    return json_cn({
        "song_id": song_id,
        "song_title": song_title,
        "duration": duration,
        "duration_formatted": format_time(duration),
        "album_id": album_id,
        "album_title": album_title,
        "singers": singers,
        "comment_count": len(comments),
        "comments": comments
    })