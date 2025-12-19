from django.db import connection

def initialize_tables():
    """
    用于修复数据库中 Django 无法设置的默认值。
    此函数会：
    """

    sql_fixes = [
        # user表
        # 修复 gender
        """
        ALTER TABLE user
        MODIFY gender ENUM('男','女','其他')
        NOT NULL DEFAULT '其他'
        """,

        # 修复 register_time
        """
        ALTER TABLE user
        MODIFY register_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复 status
        """
        ALTER TABLE user
        MODIFY status ENUM('正常','封禁中')
        NOT NULL DEFAULT '正常'
        """,

        # 修复 visibility
        """
        ALTER TABLE user
        MODIFY visibility ENUM('私密','仅关注者可见','所有人可见')
        NOT NULL DEFAULT '所有人可见'
        """,


        # singer表
        # 修复type
        """
        ALTER TABLE singer
        MODIFY type ENUM('男','女','组合')
        NOT NULL
        """,


        # album表
        # 修改表中错误的外键名字
        """
        ALTER TABLE album
        DROP FOREIGN KEY Album_singer_id_id_a2beeda4_fk_Singer_singer_id;

        ALTER TABLE album
        CHANGE COLUMN singer_id_id singer_id INT NOT NULL;

        ALTER TABLE album
        ADD CONSTRAINT Album_singer_id_fk FOREIGN KEY (singer_id) REFERENCES singer(singer_id);
        """,

        # 修复发行日期
        """
        ALTER TABLE album
        MODIFY release_date DATE
        NOT NULL DEFAULT '1970-01-01'
        """,

        # 修复专辑封面路径
        """
        ALTER TABLE album
        MODIFY cover_url VARCHAR(255)
        NOT NULL DEFAULT '/images/default_album_cover.jpg'
        """,


        # song表
        # 修改表中错误的外键名字
        """
        ALTER TABLE song
        DROP FOREIGN KEY Song_album_id_id_0b342a3e_fk_Album_album_id;

        ALTER TABLE song
        CHANGE COLUMN album_id_id album_id INT NOT NULL;

        ALTER TABLE song
        ADD CONSTRAINT Song_album_id_fk FOREIGN KEY (album_id) REFERENCES album(album_id);
        """,

        # 修复歌曲总播放次数
        """
        ALTER TABLE song
        MODIFY play_count INT
        NOT NULL DEFAULT 0
        """,

        # songlist表
        # 修改表中错误的外键名字
        """
        ALTER TABLE songlist
        DROP FOREIGN KEY Songlist_user_id_id_c4283d81_fk_User_user_id;

        ALTER TABLE songlist
        CHANGE COLUMN user_id_id user_id INT NOT NULL;

        ALTER TABLE songlist
        ADD CONSTRAINT Songlist_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id);
        """,

        # 修复创建时间
        """
        ALTER TABLE songlist
        MODIFY create_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复封面路径
        """
        ALTER TABLE songlist
        MODIFY cover_url VARCHAR(255)
        NOT NULL DEFAULT '/images/default_songlist_cover.jpg'
        """,

        # 修复点赞数
        """
        ALTER TABLE songlist
        MODIFY like_count INT
        NOT NULL DEFAULT 0
        """,

        # 修复公开性
        """
        ALTER TABLE songlist
        MODIFY is_public TINYINT
        NOT NULL DEFAULT true
        """,


        # comment表
        # 修改表中错误的外键名字
        """
        ALTER TABLE comment
        DROP FOREIGN KEY Comment_user_id_id_92454809_fk_User_user_id;

        ALTER TABLE comment
        CHANGE COLUMN user_id_id user_id INT NOT NULL;

        ALTER TABLE comment
        ADD CONSTRAINT Comment_user_id_fk FOREIGN KEY (user_id) REFERENCES user(user_id);
        """,

        # 修复评论目标类型
        """
        ALTER TABLE comment.py
        MODIFY target_type ENUM('song','album','songlist') 
        """,

        # 修复点赞数
        """
        ALTER TABLE comment.py
        MODIFY like_count INT
        NOT NULL DEFAULT 0
        """,

        # 修复评论时间
        """
        ALTER TABLE comment.py
        MODIFY comment_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复评论状态
        """
        ALTER TABLE comment.py
        MODIFY status ENUM('审核中','举报中','正常')
        NOT NULL
        """,


        # favorite表
        # 修复收藏目标类型
        """
        ALTER TABLE favorite
        MODIFY target_type ENUM('song','album','songlist') 
        """,

        # 修复收藏时间
        """
        ALTER TABLE favorite
        MODIFY favorite_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # playhistory表
        # 修复播放时间
        """
        ALTER TABLE playhistory
        MODIFY play_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修复实际播放时长
        """
        ALTER TABLE playhistory
        MODIFY play_duration INT
        NOT NULL DEFAULT 0
        """,


        # userfollow表
        # 修复关注时间
        """
        ALTER TABLE userfollow
        MODIFY follow_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # singerfollow表
        # 修复关注时间
        """
        ALTER TABLE singerfollow
        MODIFY follow_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # songlist_song表
        # 修复添加时间
        """
        ALTER TABLE songlist_song
        MODIFY add_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,


        # systemlog表
        # 修复操作时间
        """
        ALTER TABLE systemlog
        MODIFY action_time DATETIME(6)
        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        """,

        # 修改操作结果状态
        """
        ALTER TABLE systemlog
        MODIFY result ENUM('success','fail')
        NOT NULL
        """,
    ]

    with connection.cursor() as cursor:
        for sql in sql_fixes:
            try:
                cursor.execute(sql)
            except Exception as e:
                # 如果已修复或云数据库不允许重复修改，则忽略错误
                print(f"[InitialTable] Warning: {e}")

    print("[InitialTable] 建表初始化成功.")
