from django.db import models

# Create your models here.
class User(models.Model):
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
        ('其他', '其他'),
    ]

    STATUS_CHOICES = [
        ('正常', '正常'),
        ('封禁中', '封禁中'),
    ]

    user_id         = models.AutoField(primary_key=True,                                        verbose_name='用户编号')
    user_name       = models.CharField(max_length=60, unique=True,                                verbose_name='用户名')
    password        = models.CharField(max_length=64,                                       verbose_name='加密存储密码')
    gender          = models.CharField(max_length=2, choices=GENDER_CHOICES, default='其他',        verbose_name='性别')
    birthday        = models.DateField(null=True, blank=True,                                   verbose_name='出生日期')
    region          = models.CharField(max_length=50, null=True, blank=True,                    verbose_name='所在地区')
    email           = models.CharField(max_length=50, unique=True, null=True, blank=True,       verbose_name='用户邮箱')
    register_time   = models.DateTimeField(auto_now_add=True,                                   verbose_name='注册时间')
    profile         = models.CharField(max_length=768, null=True, blank=True,                   verbose_name='个人简介')
    status          = models.CharField(max_length=3, choices=STATUS_CHOICES, default='正常',    verbose_name='账号状态')

    class Meta:
        db_table = 'User'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user_name
    


class Singer(models.Model):
    TYPE_CHOICES = [
        ('男', '男'),
        ('女', '女'),
        ('组合', '组合'),
    ]

    singer_id       = models.AutoField(primary_key=True,                        verbose_name='歌手编号')
    singer_name      = models.CharField(max_length=60,                           verbose_name='歌手名称')
    type            = models.CharField(max_length=2, choices=TYPE_CHOICES,      verbose_name='歌手类型')
    country         = models.CharField(max_length=20, null=True, blank=True,        verbose_name='国籍')
    birthday        = models.DateField(null=True, blank=True,                   verbose_name='出生日期')
    introduction    = models.CharField(max_length=3072, null=True, blank=True,  verbose_name='歌手简介')

    class Meta:
        db_table = 'Singer'
        verbose_name = '歌手'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.singer_name



class Album(models.Model):
    album_id        = models.AutoField(primary_key=True,                                                verbose_name='专辑编号')
    album_title      = models.CharField(max_length=192,                                                  verbose_name='专辑名称')
    singer       = models.ForeignKey('Singer', on_delete=models.CASCADE,                             verbose_name='所属歌手')
    release_date    = models.DateField(default='1970-01-01',                                            verbose_name='发行日期')
    cover_url       = models.CharField(max_length=255, default='/images/default_album_cover.jpg',   verbose_name='专辑封面路径')
    description     = models.CharField(max_length=3072, null=True, blank=True,                          verbose_name='专辑简介')

    class Meta:
        db_table = 'Album'
        verbose_name = '专辑'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.album_title



class Song(models.Model):
    song_id     = models.AutoField(primary_key=True,                    verbose_name='歌曲编号')
    song_title  = models.CharField(max_length=192,                      verbose_name='歌曲名称')
    album    = models.ForeignKey('Album', on_delete=models.CASCADE,  verbose_name='所属专辑')
    duration    = models.IntegerField(                                  verbose_name='歌曲时长')
    file_url    = models.CharField(max_length=255,                  verbose_name='音频文件路径')
    play_count  = models.IntegerField(default=0,                  verbose_name='歌曲播放总次数')

    class Meta:
        db_table = 'Song'
        verbose_name = '歌曲'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.song_title



class Songlist(models.Model):
    songlist_id     = models.AutoField(primary_key=True,                                                verbose_name='歌单编号')
    songlist_title  = models.CharField(max_length=192,                                                  verbose_name='歌单名称')
    user         = models.ForeignKey('User', on_delete=models.CASCADE,                               verbose_name='创建者ID')
    description     = models.CharField(max_length=3072,  null=True, blank=True,                         verbose_name='歌单简介')
    create_time     = models.DateTimeField(auto_now_add=True,                                           verbose_name='创建时间')
    cover_url       = models.CharField(max_length=255, default='/images/default_songlist_cover.jpg',    verbose_name='封面路径')
    like_count      = models.IntegerField(default=0,                                                      verbose_name='点赞数')
    is_public       = models.BooleanField(default=True,                                                 verbose_name='是否公开')

    class Meta:
        db_table = 'Songlist'
        verbose_name = '歌单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.songlist_title



class Comment(models.Model):
    TARGET_TYPE_CHOICES = [
        ('song', 'song'),
        ('album', 'album'),
        ('songlist', 'songlist'),
    ]

    STATUS_CHOICES = [
        ('审核中', '审核中'),
        ('举报中', '举报中'),
        ('正常', '正常'),
    ]

    comment_id      = models.AutoField(primary_key=True,                                verbose_name='评论编号')
    user         = models.ForeignKey('User', on_delete=models.CASCADE,               verbose_name='评论用户')
    target_type     = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES,   verbose_name='评论目标类型')
    content         = models.CharField(max_length=300,                                  verbose_name='评论内容')
    like_count      = models.IntegerField(default=0,                                      verbose_name='点赞数')
    comment_time    = models.DateTimeField(auto_now_add=True,                           verbose_name='评论时间')
    parent_id       = models.IntegerField(null=True, blank=True,                        verbose_name='父评论ID')
    status          = models.CharField(max_length=3, choices=STATUS_CHOICES,            verbose_name='评论状态')
    target_id       = models.IntegerField(verbose_name='评论目标ID')

    class Meta:
        db_table = 'Comment'
        verbose_name = '评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.comment_id



class Favorite(models.Model):
    TARGET_TYPE_CHOICES = [
        ('song', 'song'),
        ('album', 'album'),
        ('songlist', 'songlist'),
    ]

    favorite_id     = models.AutoField(primary_key=True,                            verbose_name='收藏记录编号')
    user            = models.ForeignKey('User', on_delete=models.CASCADE,               verbose_name='收藏用户')
    target_type     = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES,  verbose_name='收藏对象类型')
    target_id       = models.IntegerField(                                            verbose_name='收藏对象ID')
    favorite_time   = models.DateTimeField(auto_now_add=True,                           verbose_name='收藏时间')

    class Meta:
        db_table = 'Favorite'

    def __str__(self):
        return self.favorite_id



class PlayHistory(models.Model):
    play_id         = models.AutoField(primary_key=True,                verbose_name='播放记录编号')
    user            = models.ForeignKey('User', on_delete=models.CASCADE,   verbose_name='播放用户')
    song            = models.ForeignKey('Song', on_delete=models.CASCADE,   verbose_name='播放歌曲')
    play_time       = models.DateTimeField(auto_now_add=True,               verbose_name='播放时间')
    play_duration   = models.IntegerField(                        verbose_name='实际播放时长（秒）')

    class Meta:
        db_table = 'PlayHistory'

    def __str__(self):
        return self.play_id



class UserFollow(models.Model):
    follower    = models.ForeignKey('User', on_delete=models.CASCADE, related_name='following', verbose_name='关注者用户')
    followed    = models.ForeignKey('User', on_delete=models.CASCADE, related_name='followers', verbose_name='被关注用户')
    follow_time = models.DateTimeField(auto_now_add=True,                                         verbose_name='关注时间')

    class Meta:
        db_table = 'UserFollow'
        unique_together = (('follower', 'followed'),)   #primary_key

    def __str__(self):
        return self.follower + ' ' + self.followed



class SingerFollow(models.Model):
    user        = models.ForeignKey('User', on_delete=models.CASCADE,     verbose_name='关注用户')
    singer      = models.ForeignKey('Singer', on_delete=models.CASCADE, verbose_name='被关注歌手')
    follow_time = models.DateTimeField(auto_now_add=True,                 verbose_name='关注时间')

    class Meta:
        db_table = 'SingerFollow'
        unique_together = (('user', 'singer'),)     #primary_key

    def __str__(self):
        return self.user + ' ' + self.singer



class SonglistSong(models.Model):
    songlist = models.ForeignKey('Songlist', on_delete=models.CASCADE, verbose_name='歌单ID')
    song     = models.ForeignKey('Song', on_delete=models.CASCADE,     verbose_name='歌曲ID')
    add_time = models.DateTimeField(auto_now_add=True,               verbose_name='添加时间')

    class Meta:
        db_table = 'Songlist_Song'
        unique_together = (('songlist', 'song'),)     #primary_key

    def __str__(self):
        return self.songlist + ' ' + self.song



class SongSinger(models.Model):
    song   = models.ForeignKey('Song', on_delete=models.CASCADE,    verbose_name='歌曲ID')
    singer = models.ForeignKey('Singer', on_delete=models.CASCADE,  verbose_name='歌手ID')

    class Meta:
        db_table = 'Song_Singer'
        unique_together = (('song', 'singer'),)     #primary_key

    def __str__(self):
        return self.song + ' ' + self.singer    



class SystemLog(models.Model):   
    RESULT_CHOICES = [
        ('success', 'success'),
        ('fail', 'fail'),
    ]

    log_id       = models.AutoField(primary_key=True,                           verbose_name='日志编号')
    action       = models.CharField(max_length=255,                             verbose_name='操作内容')
    target_table = models.CharField(max_length=64, null=True, blank=True, verbose_name='被操作数据表名')
    target_id    = models.IntegerField(null=True, blank=True,               verbose_name='被操作记录ID')
    action_time  = models.DateTimeField(auto_now_add=True,                      verbose_name='操作时间')
    result       = models.CharField(max_length=10, choices=RESULT_CHOICES,  verbose_name='操作结果状态')
    class Meta:
        db_table = 'SystemLog'


#删表sql指令
#DROP TABLE singerfollow;
#DROP TABLE songlist_song;
#DROP TABLE song_singer;
#DROP TABLE userfollow;
#DROP TABLE comment.py;
#DROP TABLE favorite;
#DROP TABLE Playhistory;
#DROP TABLE songlist;
#DROP TABLE user;
#DROP TABLE systemlog;
#DROP TABLE song;
#DROP TABLE album;
#DROP TABLE singer;
#DROP TABLE django_session;
#DROP TABLE django_migrations;
#DROP TABLE django_admin_log;
#DROP TABLE auth_group_permissions;
#DROP TABLE auth_user_groups;
#DROP TABLE auth_group; 
#DROP TABLE auth_user_user_permissions; 
#DROP TABLE auth_user;
#DROP TABLE auth_permission;
#DROP TABLE django_content_type; 