# 播放记录模块
import json
import datetime
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from .tools import *


# 记录播放
# 设置防刷规则：同一首歌在 60秒 内重复提交只记录一次，不增加播放计数
# 自动更新 Song 表的 play_count
@csrf_exempt
def record_play(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    song_id = data.get("song_id")
    # 实际播放时长（秒），如果前端没传，默认0
    play_duration = data.get("play_duration", 0)

    if not song_id:
        return json_cn({"error": "未检测到歌曲ID"}, 400)

    with connection.cursor() as cursor:
        # 规则检查：防止重复记录 (Anti-Spam)
        # 检查该用户最近一次播放这首歌的时间
        sql_check_recent = """
                           SELECT play_time
                           FROM PlayHistory
                           WHERE user_id = %s \
                             AND song_id = %s
                           ORDER BY play_time DESC
                           LIMIT 1 \
                           """
        cursor.execute(sql_check_recent, [current_user_id, song_id])
        last_record = cursor.fetchone()

        should_record = True

        if last_record:
            last_time = last_record[0]
            # 获取当前时间 (注意时区问题，这里假设数据库和应用时区一致)
            # 如果最近一次播放是在 60秒 内，则认为是重复提交或者是切歌太快，不计入有效播放
            # 也可以根据 play_duration 判断，例如播放超过30秒才算
            now = datetime.datetime.now()
            if (now - last_time).total_seconds() < 60:
                should_record = False

        if should_record:
            # 1. 插入播放记录
            sql_insert = """
                         INSERT INTO PlayHistory (user_id, song_id, play_duration, play_time)
                         VALUES (%s, %s, %s, NOW()) \
                         """
            cursor.execute(sql_insert, [current_user_id, song_id, play_duration])

            # 2. 更新歌曲总播放次数 (原子更新)
            sql_update_song = """
                              UPDATE Song \
                              SET play_count = play_count + 1 \
                              WHERE song_id = %s \
                              """
            cursor.execute(sql_update_song, [song_id])

            return json_cn({"message": "播放记录已更新"})
        else:
            return json_cn({"message": "播放记录过频，忽略本次计数"})

# 统计总播放次数 (歌曲、专辑、歌手)
def get_total_play_stats(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    target_type = request.GET.get("target_type")  # song, album, singer
    target_id = request.GET.get("target_id")

    if not target_type or not target_id:
        return json_cn({"error": "参数缺失"}, 400)

    count = 0
    with connection.cursor() as cursor:
        if target_type == 'song':
            # 直接查 Song 表
            sql = "SELECT play_count FROM Song WHERE song_id = %s"
            cursor.execute(sql, [target_id])
            row = cursor.fetchone()
            count = row[0] if row else 0

        elif target_type == 'album':
            # 统计该专辑下所有歌曲的播放数总和
            sql = """
                  SELECT SUM(play_count) \
                  FROM Song \
                  WHERE album_id = %s \
                  """
            cursor.execute(sql, [target_id])
            row = cursor.fetchone()
            count = row[0] if row and row[0] else 0

        elif target_type == 'singer':
            # 统计该歌手名下所有歌曲的播放数总和
            # 需要通过 Song_Singer 中间表关联 (或者 Song -> Album -> Singer)
            # 这里使用 Song_Singer 表更准确，因为包括了 feat 的歌曲
            sql = """
                  SELECT SUM(s.play_count)
                  FROM Song s
                           JOIN Song_Singer ss ON s.song_id = ss.song_id
                  WHERE ss.singer_id = %s \
                  """
            cursor.execute(sql, [target_id])
            row = cursor.fetchone()
            count = row[0] if row and row[0] else 0

        else:
            return json_cn({"error": "无效类型"}, 400)

    return json_cn({
        "target_type": target_type,
        "target_id": target_id,
        "total_play_count": count
    })


# 用户查看播放记录 (支持整体、筛选、查单曲)
def get_my_play_history(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # 筛选参数
    start_date = data.get("start_date")  # 格式 'YYYY-MM-DD'
    end_date = data.get("end_date")
    song_id = data.get("song_id")  # 如果传了这个，就是查看单曲的播放记录
    limit = data.get("limit", 50)  # 默认只看最近50条

    sql = """
          SELECT ph.play_id, \
                 ph.play_time, \
                 ph.play_duration,
                 s.song_id, \
                 s.song_title, \
                 s.file_url,
                 a.album_title, \
                 a.cover_url
          FROM PlayHistory ph
                   JOIN Song s ON ph.song_id = s.song_id
                   LEFT JOIN Album a ON s.album_id = a.album_id
          WHERE ph.user_id = %s \
          """
    params = [current_user_id]

    if start_date:
        sql += " AND ph.play_time >= %s"
        params.append(start_date)

    if end_date:
        # 结束日期通常要加一天或者到 23:59:59，这里简单处理
        sql += " AND ph.play_time <= %s"
        params.append(end_date + " 23:59:59")

    if song_id:
        sql += " AND ph.song_id = %s"
        params.append(song_id)

    sql += " ORDER BY ph.play_time DESC LIMIT %s"
    params.append(limit)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        history = dictfetchall(cursor)

    return json_cn({"history": history, "count": len(history)})


# 生成用户播放报告 (周/月/自定义时间段)
# 统计该时间段内：总播放次数、总听歌时长、听得最多的歌
def get_play_report(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # time_range: 'week', 'month', 'all'
    time_range = data.get("time_range", "week")

    # 构建时间条件
    sql_where = "WHERE user_id = %s"
    params = [current_user_id]

    if time_range == 'week':
        # 最近7天
        sql_where += " AND play_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    elif time_range == 'month':
        # 最近30天
        sql_where += " AND play_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    elif time_range == 'self-defined':
        if "start_date" in data:
            sql_where += " AND play_time >= %s"
            params.append(data.get("start_date"))
        if "end_date" in data:
            sql_where += " AND play_time <= %s"
            params.append(data.get("end_date"))

    with connection.cursor() as cursor:
        # 1. 统计总次数和总时长
        sql_summary = f"""
            SELECT COUNT(*) as total_count, SUM(play_duration) as total_seconds
            FROM PlayHistory
            {sql_where}
        """
        cursor.execute(sql_summary, params)
        summary = dictfetchall(cursor)[0]

        # 处理 None 的情况
        if not summary['total_seconds']: summary['total_seconds'] = 0

        # 2. 统计该时间段内听得最多的歌 (Top 1)
        sql_top_song = f"""
            SELECT s.song_title, COUNT(ph.song_id) as play_times
            FROM PlayHistory ph
            JOIN Song s ON ph.song_id = s.song_id
            {sql_where.replace('WHERE', 'WHERE ph.')} 
            GROUP BY ph.song_id, s.song_title
            ORDER BY play_times DESC
            LIMIT 1
        """
        # 注意：这里 user_id 参数需要再传一遍，或者稍微调整 SQL 拼接逻辑
        # 为简单起见，这里复用 params
        cursor.execute(sql_top_song, params)
        top_song_row = dictfetchall(cursor)
        top_song = top_song_row[0] if top_song_row else None

    return json_cn({
        "time_range": time_range,
        "report": {
            "total_plays": summary['total_count'],
            "total_duration_minutes": round(summary['total_seconds'] / 60, 2),
            "top_song": top_song
        }
    })


# 用户最常听排行榜 (歌手/专辑/歌曲)
# 展示“我”最爱听的
def get_user_top_charts(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # type: 'song', 'singer', 'album'
    chart_type = data.get("type", "song")
    limit = data.get("limit", 10)

    with connection.cursor() as cursor:
        if chart_type == 'song':
            sql = """
                  SELECT s.song_id, s.song_title, s.file_url, COUNT(*) as my_play_count
                  FROM PlayHistory ph
                           JOIN Song s ON ph.song_id = s.song_id
                  WHERE ph.user_id = %s
                  GROUP BY s.song_id, s.song_title, s.file_url
                  ORDER BY my_play_count DESC
                  LIMIT %s \
                  """
            cursor.execute(sql, [current_user_id, limit])

        elif chart_type == 'album':
            sql = """
                  SELECT a.album_id, a.album_title, a.cover_url, COUNT(*) as my_play_count
                  FROM PlayHistory ph
                           JOIN Song s ON ph.song_id = s.song_id
                           JOIN Album a ON s.album_id = a.album_id
                  WHERE ph.user_id = %s
                  GROUP BY a.album_id, a.album_title, a.cover_url
                  ORDER BY my_play_count DESC
                  LIMIT %s \
                  """
            cursor.execute(sql, [current_user_id, limit])

        elif chart_type == 'singer':
            # 这里需要关联 Song -> SongSinger -> Singer
            sql = """
                  SELECT singer.singer_id, singer.singer_name, COUNT(*) as my_play_count
                  FROM PlayHistory ph
                           JOIN Song s ON ph.song_id = s.song_id
                           JOIN Song_Singer ss ON s.song_id = ss.song_id
                           JOIN Singer singer ON ss.singer_id = singer.singer_id
                  WHERE ph.user_id = %s
                  GROUP BY singer.singer_id, singer.singer_name
                  ORDER BY my_play_count DESC
                  LIMIT %s \
                  """
            cursor.execute(sql, [current_user_id, limit])

        else:
            return json_cn({"error": "无效的榜单类型"}, 400)

        result = dictfetchall(cursor)

    return json_cn({
        "chart_type": chart_type,
        "list": result
    })


# 用户时间段内播放情况统计 (趋势图数据)
# 用于前端画图，例如：统计最近7天，每天听了多少首
def get_user_activity_trend(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # period: 'day' (最近14天, 按天统计), 'month' (最近12个月, 按月统计)
    period = data.get("period", "day")

    with connection.cursor() as cursor:
        if period == 'day':
            # 按日期分组统计
            sql = """
                  SELECT DATE_FORMAT(play_time, '%%Y-%%m-%%d') as date_str, COUNT(*) as play_count
                  FROM PlayHistory
                  WHERE user_id = %s \
                    AND play_time >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                  GROUP BY date_str
                  ORDER BY date_str ASC \
                  """
        elif period == 'month':
            # 按月份分组统计
            sql = """
                  SELECT DATE_FORMAT(play_time, '%%Y-%%m') as date_str, COUNT(*) as play_count
                  FROM PlayHistory
                  WHERE user_id = %s \
                    AND play_time >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                  GROUP BY date_str
                  ORDER BY date_str ASC \
                  """
        else:
            return json_cn({"error": "Invalid period"}, 400)

        # 注意：Python 中 % 是占位符，所以在 SQL 里的 %Y 需要写成 %%Y 进行转义
        cursor.execute(sql, [current_user_id])
        trend_data = dictfetchall(cursor)

    return json_cn({
        "period": period,
        "trend": trend_data
    })