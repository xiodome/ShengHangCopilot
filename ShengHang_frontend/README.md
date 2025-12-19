# 声航音乐前端

这是声航音乐服务系统的前端部分，使用纯HTML + CSS + JavaScript实现。

## 结构

```
ShengHang_frontend/
├── css/
│   └── style.css          # 全局样式文件
├── js/
│   └── api.js             # API封装和工具函数
├── index.html             # 首页
├── login.html             # 登录页面
├── register.html          # 注册页面
├── music.html             # 音乐中心（搜索歌曲/歌手/专辑）
├── songlist.html          # 歌单管理
├── favorites.html         # 我的收藏
├── history.html           # 播放记录
├── profile.html           # 个人中心
├── admin.html             # 管理员后台
└── README.md              # 说明文档
```

## 功能模块

### 1. 用户认证
- 用户注册（login.html）
- 用户登录（register.html）
- 登出功能

### 2. 首页 (index.html)
- 快速搜索功能
- 本周听歌报告
- 最爱歌曲排行
- 统计卡片（播放数、收藏数等）

### 3. 音乐中心 (music.html)
- 歌曲搜索
- 歌手搜索
- 专辑搜索
- 详情查看
- 收藏功能
- 添加到歌单
- 评论功能

### 4. 歌单管理 (songlist.html)
- 创建歌单
- 编辑歌单
- 删除歌单
- 添加/移除歌曲
- 歌单排序
- 评论功能

### 5. 我的收藏 (favorites.html)
- 收藏的歌曲
- 收藏的专辑
- 收藏的歌单
- 取消收藏

### 6. 播放记录 (history.html)
- 最近播放
- 听歌报告
- 我的排行榜（歌曲/歌手/专辑）
- 播放趋势图

### 7. 个人中心 (profile.html)
- 个人资料查看/编辑
- 修改密码
- 关注管理（关注用户/粉丝/关注歌手）
- 我的评论
- 注销账号

### 8. 管理员后台 (admin.html)
- 歌手管理（添加/删除）
- 专辑管理（添加/删除）
- 歌曲管理（添加/删除）



## 注意事项

1. **CORS配置**: 后端已添加CORS支持（django-cors-headers），需要确保已安装：
   ```bash
   pip install django-cors-headers
   ```

2. **Session认证**: 前端使用localStorage存储用户信息，后端使用Session进行认证。

3. **管理员权限**: 管理员功能需要使用管理员账号`user_id=ADMIN_USER_ID`登录。

## 技术栈

- HTML5
- CSS3 (响应式设计)
- JavaScript (ES6+)
- Fetch API

