# app/urls.py
from django.urls import path
from app.views import user as user
from app.views import music as music
from app.views import favoriteAndSonglist as favorite
from app.views import comment as comment
from app.views import playhistory as ph
from app.views import manager as manager

from django.http import HttpResponse

def home(request):
    return HttpResponse("ShengHang backend is running successfully.")



urlpatterns = [
    path("", home),
    # 用户管理模块
    path("user/register/", user.register),
    path("user/login/", user.login),
    path("user/logout/", user.logout),
    path("user/delete_account/", user.delete_account),
    path("user/change_password/", user.change_password),
    path("user/profile/<int:owner_id>/", user.profile),
    path("user/update_profile/", user.update_profile),
    path("user/follow_user/", user.follow_user),
    path("user/unfollow_user/", user.unfollow_user),
    path("user/follow_singer/", user.follow_singer),
    path("user/unfollow_singer/", user.unfollow_singer),
    path("user/<int:uid>/get_followers/", user.get_followers),
    path("user/<int:uid>/get_followings/", user.get_followings),
    path("user/<int:uid>/get_followsingers/", user.get_followsingers),
    path("user/get_user_info/", user.get_user_info),
    path("Administrator/profile/", user.admin_profile),
    path("user/update_visibility", user.update_visibility),

    # 歌手与音乐管理模块
    path("music/", music.music),
    path("singer/search_singer/", music.search_singer),
    path("singer/profile/<int:singer_id>/", music.singer_profile),
    path("album/search_album/", music.search_album),
    path("album/profile/<int:album_id>/", music.album_profile),
    path("song/search_song/", music.search_song),
    path("song/profile/<int:song_id>/", music.song_profile),

    # 收藏与歌单模块
    path("songlist/list_songlists/", favorite.list_songlists),
    path("songlist/create_songlist/", favorite.create_songlist),
    path("songlist/edit_songlist/<int:songlist_id>/", favorite.edit_songlist),
    path("songlist/profile/<int:songlist_id>/", favorite.songlist_profile),
    path("songlist/delete_songlist/<int:songlist_id>/", favorite.delete_songlist),
    path("songlist/<int:songlist_id>/add_song/", favorite.songlist_add_song),
    path("songlist/<int:songlist_id>/delete_song/<int:song_id>/", favorite.songlist_delete_song),
    path("songlist/sort_songlist/<int:songlist_id>/", favorite.sort_songlist),
    path("songlist/search_songlist/", favorite.search_songlist),
    path("songlist/like_songlist/<int:songlist_id>/", favorite.like_songlist),
    path("favorite/list_favorite/", favorite.list_favorite),
    path("favorite/add_favorite/", favorite.add_favorite),
    path("favorite/delete_favorite/", favorite.delete_favorite),
    path("favorite/get_my_favorite_songs_stats/", favorite.get_my_favorite_songs_stats),
    path("favorite/get_platform_top_favorites/", favorite.get_platform_top_favorites),

    # 评论模块
    path("comment/list_comment/", comment.list_comment),
    path("comment/publish_comment/", comment.publish_comment),
    path("comment/delete_comment/", comment.delete_comment),
    path("comment/action_comment/", comment.action_comment),
    path("comment/get_comments_by_target/", comment.get_comments_by_target),
    path("comment/get_comment_detail/", comment.get_comment_detail),
    path("comment/get_my_comments/", comment.get_my_comments),
    path("comment/get_comment_stats/", comment.get_comment_stats),
    path("comment/report_comment/", comment.report_comment),

    # 播放记录模块
    path("playHistory/record_play/", ph.record_play),
    path("playHistory/get_total_play_stats/", ph.get_total_play_stats),
    path("playHistory/get_my_play_history/", ph.get_my_play_history),
    path("playHistory/get_play_report/", ph.get_play_report),
    path("playHistory/get_user_top_charts/", ph.get_user_top_charts),
    path("playHistory/get_user_activity_trend/", ph.get_user_activity_trend),


    # 管理员管理模块
    path("Administrator/singer/admin_add_singer/", manager.admin_add_singer),
    path("Administrator/singer/admin_delete_singer/", manager.admin_delete_singer),
    path("Administrator/singer/admin_update_singer/", manager.admin_update_singer),
    path("Administrator/album/admin_add_album/", manager.admin_add_album),
    path("Administrator/album/admin_delete_album/", manager.admin_delete_album),
    path("Administrator/album/admin_update_album/", manager.admin_update_album),
    path("Administrator/song/admin_add_song/", manager.admin_add_song),
    path("Administrator/song/admin_delete_song/", manager.admin_delete_song),
    path("Administrator/song/admin_update_song/", manager.admin_update_song),
    path("Administrator/get_system_logs/", manager.get_system_logs),
    path("Administrator/user/get_specific_user_stats/", manager.get_specific_user_stats),
    path("Administrator/user/get_user_behavior_stats/", manager.get_user_behavior_stats),
    path("Administrator/comment/get_user_behavior_stats/", manager.admin_get_pending_comments),
    path("Administrator/comment/admin_audit_comment/", manager.admin_audit_comment),
]
