/**
 * 声航音乐服务系统 - API封装
 */

// API基础配置 - 可通过修改此值来适配不同环境
// 开发环境: 'http://127.0.0.1:8000'
// 生产环境: 根据实际部署地址修改
const API_BASE_URL = 'http://127.0.0.1:8000'; //window.API_BASE_URL ||

// 存储用户信息 - 注意：生产环境应使用更安全的认证方式(如httpOnly cookies)
// localStorage仅用于开发和演示目的
const UserStore = {
    getUserId: () => sessionStorage.getItem('user_id'),
    getUsername: () => sessionStorage.getItem('username'),
    isAdmin: () => sessionStorage.getItem('is_admin') === 'true',
    setUser: (userId, username, isAdmin) => {
        sessionStorage.setItem('user_id', userId);
        sessionStorage.setItem('username', username);
        sessionStorage.setItem('is_admin', isAdmin);
    },
    clearUser: () => {
        sessionStorage.removeItem('user_id');
        sessionStorage.removeItem('username');
        sessionStorage.removeItem('is_admin');
    },
    isLoggedIn: () => sessionStorage.getItem('user_id') !== null
};

// 通用请求函数
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        }
    };

    const finalOptions = { ...defaultOptions, ...options };
    
    if (options.body && typeof options.body === 'object') {
        finalOptions.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, finalOptions);
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error(`API Error: Expected JSON but got ${contentType || 'unknown'} for ${endpoint}`, text);
            throw { 
                status: response.status, 
                url: endpoint,
                error: `服务器返回了非JSON格式的响应: ${contentType || 'unknown'}`,
                rawResponse: text
            };
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            const errorInfo = { 
                status: response.status, 
                url: endpoint,
                ...data 
            };
            console.error(`API Error: HTTP ${response.status} for ${endpoint}`, data);
            throw errorInfo;
        }
        
        return data;
    } catch (error) {
        if (error.status) {
            // Already formatted API error
            throw error;
        }
        console.error('API请求错误:', error);
        throw error;
    }
}

// ====================================
// 用户管理API
// ====================================
const UserAPI = {
    // 注册
    register: (userData) => apiRequest('/user/register/', {
        method: 'POST',
        body: userData
    }),

    // 登录
    login: (username, password) => apiRequest('/user/login/', {
        method: 'POST',
        body: { username, password }
    }),

    // 登出
    logout: () => apiRequest('/user/logout/', {
        method: 'POST'
    }),

    // 删除账号
    deleteAccount: (password) => apiRequest('/user/delete_account/', {
        method: 'POST',
        body: { password }
    }),

    // 修改密码
    changePassword: (oldPassword, newPassword) => apiRequest('/user/change_password/', {
        method: 'POST',
        body: { old_password: oldPassword, new_password: newPassword }
    }),

    // 获取个人资料
    getProfile: (userId) => apiRequest(`/user/profile/${userId}/`, {
        method: 'GET'
    }),

    // 更新个人资料
    updateProfile: (profileData) => apiRequest('/user/update_profile/', {
        method: 'POST',
        body: profileData
    }),

    // 关注用户
    followUser: (userId) => apiRequest('/user/follow_user/', {
        method: 'POST',
        body: { user_id: userId }
    }),

    // 取关用户
    unfollowUser: (userId) => apiRequest('/user/unfollow_user/', {
        method: 'POST',
        body: { user_id: userId }
    }),

    // 关注歌手
    followSinger: (singerId) => apiRequest('/user/follow_singer/', {
        method: 'POST',
        body: { singer_id: singerId }
    }),

    // 取关歌手
    unfollowSinger: (singerId) => apiRequest('/user/unfollow_singer/', {
        method: 'POST',
        body: { singer_id: singerId }
    }),

    // 获取关注列表
    getFollowings: (userId) => apiRequest(`/user/${userId}/get_followings/`, {
        method: 'GET'
    }),

    // 获取粉丝列表
    getFollowers: (userId) => apiRequest(`/user/${userId}/get_followers/`, {
        method: 'GET'
    }),

    // 获取关注的歌手
    getFollowSingers: (userId) => apiRequest(`/user/${userId}/get_followsingers/`, {
        method: 'GET'
    }),

    // 根据用户名查询用户
    getUserInfo: (userName) => apiRequest('/user/get_user_info/', {
        method: 'POST',
        body: { user_name: userName }
    }),

    // 更新个人信息可见性
    updateVisibility: (visibility) => apiRequest('/user/update_visibility/', {
        method: 'POST',
        body: visibility
    })
};

// ====================================
// 音乐管理API
// ====================================
const MusicAPI = {
    // 搜索歌手
    searchSinger: (filters) => apiRequest('/singer/search_singer/', {
        method: 'POST',
        body: filters
    }),

    // 获取歌手详情
    getSingerProfile: (singerId) => apiRequest(`/singer/profile/${singerId}/`, {
        method: 'GET'
    }),

    // 搜索专辑
    searchAlbum: (filters) => apiRequest('/album/search_album/', {
        method: 'POST',
        body: filters
    }),

    // 获取专辑详情
    getAlbumProfile: (albumId) => apiRequest(`/album/profile/${albumId}/`, {
        method: 'GET'
    }),

    // 搜索歌曲
    searchSong: (filters) => apiRequest('/song/search_song/', {
        method: 'POST',
        body: filters
    }),

    // 获取歌曲详情
    getSongProfile: (songId) => apiRequest(`/song/profile/${songId}/`, {
        method: 'GET'
    })
};

// ====================================
// 歌单管理API
// ====================================
const SonglistAPI = {
    // 获取歌单列表
    listSonglists: (isPublic = null, sortBy = 'create_time') => {
        let url = '/songlist/list_songlists/?sort_by=' + sortBy;
        if (isPublic !== null) {
            url += '&is_public=' + (isPublic ? '1' : '0');
        }
        return apiRequest(url, { method: 'GET' });
    },

    // 创建歌单
    createSonglist: (songlistData) => apiRequest('/songlist/create_songlist/', {
        method: 'POST',
        body: songlistData
    }),

    // 编辑歌单
    editSonglist: (songlistId, songlistData) => apiRequest(`/songlist/edit_songlist/${songlistId}/`, {
        method: 'POST',
        body: songlistData
    }),

    // 获取歌单详情
    getSonglistProfile: (songlistId) => apiRequest(`/songlist/profile/${songlistId}/`, {
        method: 'GET'
    }),

    // 删除歌单
    deleteSonglist: (songlistId) => apiRequest(`/songlist/delete_songlist/${songlistId}/`, {
        method: 'POST'
    }),

    // 向歌单添加歌曲
    addSongToSonglist: (songlistId, songId) => apiRequest(`/songlist/${songlistId}/add_song/`, {
        method: 'POST',
        body: { song_id: songId }
    }),

    // 从歌单删除歌曲
    removeSongFromSonglist: (songlistId, songId) => apiRequest(`/songlist/${songlistId}/delete_song/${songId}/`, {
        method: 'POST'
    }),

    // 搜索歌单
    searchSonglist: (title) => apiRequest('/songlist/search_songlist/', {
        method: 'POST',
        body: { songlist_title: title }
    }),

    // 点赞歌单
    likeSonglist: (songlistId) => apiRequest(`/songlist/like_songlist/${songlistId}/`, {
        method: 'POST'
    }),

    // 歌单排序
    sortSonglist: (songlistId, sortBy) => apiRequest(`/songlist/sort_songlist/${songlistId}/?sort=${sortBy}`, {
        method: 'GET'
    })
};

// ====================================
// 收藏管理API
// ====================================
const FavoriteAPI = {
    // 获取收藏列表
    listFavorites: () => apiRequest('/favorite/list_favorite/', {
        method: 'GET'
    }),

    // 添加收藏
    addFavorite: (type, id) => apiRequest('/favorite/add_favorite/', {
        method: 'POST',
        body: { type, id }
    }),

    // 删除收藏
    deleteFavorite: (type, id) => apiRequest('/favorite/delete_favorite/', {
        method: 'POST',
        body: { type, id }
    }),

    // 获取收藏歌曲统计
    getMyFavoriteSongsStats: () => {
        console.log('调用getMyFavoriteSongsStats API');
        return apiRequest('/favorite/get_my_favorite_songs_stats/', {
            method: 'POST'
        });
    },

    // 获取平台热门收藏排行
    getPlatformTopFavorites: (targetType, limit = 10) => {
        console.log('调用getPlatformTopFavorites API:', targetType, limit);
        return apiRequest('/favorite/get_platform_top_favorites/', {
            method: 'POST',
            body: { target_type: targetType, limit }
        });
    }
};

// ====================================
// 评论管理API
// ====================================
const CommentAPI = {
    // 获取评论列表
    listComments: () => apiRequest('/comment/list_comment/', {
        method: 'GET'
    }),

    // 发布评论
    publishComment: (targetType, targetId, content, parentId = null) => apiRequest('/comment/publish_comment/', {
        method: 'POST',
        body: { target_type: targetType, target_id: targetId, content, parent_id: parentId }
    }),

    // 删除评论
    deleteComment: (commentId) => apiRequest('/comment/delete_comment/', {
        method: 'POST',
        body: { comment_id: commentId }
    }),

    // 评论操作(点赞/举报)
    actionComment: (commentId, action) => apiRequest('/comment/action_comment/', {
        method: 'POST',
        body: { comment_id: commentId, action }
    }),

    // 获取目标的评论
    getCommentsByTarget: (targetType, targetId, sortBy = 'time') => 
        apiRequest(`/comment/get_comments_by_target/?target_type=${targetType}&target_id=${targetId}&sort_by=${sortBy}`, {
            method: 'GET'
        }),

    // 获取评论详情
    getCommentDetail: (commentId) => apiRequest(`/comment/get_comment_detail/?comment_id=${commentId}`, {
        method: 'GET'
    }),

    // 获取我的评论
    getMyComments: () => apiRequest('/comment/get_my_comments/', {
        method: 'GET'
    }),

    // 获取评论统计
    getCommentStats: (targetType, targetId) => 
        apiRequest(`/comment/get_comment_stats/?target_type=${targetType}&target_id=${targetId}`, {
            method: 'GET'
        }),

    // 举报评论
    reportComment: (commentId, reason = '') => 
        apiRequest('/comment/report_comment/', {
            method: 'POST',
            body: { comment_id: commentId, reason }
        })
};

// ====================================
// 播放记录API
// ====================================
DEFALUT_PLAY_DURATION = Math.min(Math.floor(-Math.log(1 - Math.random()) * 150 + 40), 360); // 播放时长范围：40-360秒 平均：150秒
const PlayHistoryAPI = {
    // 记录播放
    recordPlay: (songId, playDuration = 0) => apiRequest('/playHistory/record_play/', {
        method: 'POST',
        body: { song_id: songId, play_duration: DEFALUT_PLAY_DURATION }
    }),

    // 获取播放统计
    getTotalPlayStats: (targetType, targetId) => 
        apiRequest(`/playHistory/get_total_play_stats/?target_type=${targetType}&target_id=${targetId}`, {
            method: 'GET'
        }),

    // 获取我的播放历史
    getMyPlayHistory: (filters = {}) => apiRequest('/playHistory/get_my_play_history/', {
        method: 'POST',
        body: filters
    }),

    // 获取播放报告
    getPlayReport: (timeRange = 'week', startDate = null, endDate = null) => {
        const body = { time_range: timeRange };
        if (startDate) body.start_date = startDate;
        if (endDate) body.end_date = endDate;
        return apiRequest('/playHistory/get_play_report/', {
            method: 'POST',
            body
        });
    },

    // 获取用户排行榜
    getUserTopCharts: (type = 'song', limit = 10) => apiRequest('/playHistory/get_user_top_charts/', {
        method: 'POST',
        body: { type, limit }
    }),

    // 获取用户活动趋势
    getUserActivityTrend: (period = 'day') => apiRequest('/playHistory/get_user_activity_trend/', {
        method: 'POST',
        body: { period }
    })
};


const AdministratorAPI = {
    // 添加歌手
    adminAddSinger: (singerData) => apiRequest('/Administrator/singer/admin_add_singer/', {
        method: 'POST',
        body: singerData
    }),

    // 删除歌手
    adminDeleteSinger: (singerId, singerName) => apiRequest('/Administrator/singer/admin_delete_singer/', {
        method: 'POST',
        body: { singer_id: singerId, singer_name: singerName }
    }),

    // 修改歌手信息
    adminUpdateSinger: (singerData) => apiRequest('/Administrator/singer/admin_update_singer/', {
        method: 'POST',
        body: singerData
    }),

    // 添加专辑
    adminAddAlbum: (albumData) => apiRequest('/Administrator/album/admin_add_album/', {
        method: 'POST',
        body: albumData
    }),

    // 删除专辑
    adminDeleteAlbum: (albumId) => apiRequest('/Administrator/album/admin_delete_album/', {
        method: 'POST',
        body: { album_id: albumId }
    }),

    // 修改专辑信息
    adminUpdateAlbum: (albumData) => apiRequest('/Administrator/album/admin_update_album/', {
        method: 'POST',
        body: albumData
    }),

    // 添加歌曲
    adminAddSong: (songData) => apiRequest('/Administrator/song/admin_add_song/', {
        method: 'POST',
        body: songData
    }),

    // 删除歌曲
    adminDeleteSong: (songId) => apiRequest('/Administrator/song/admin_delete_song/', {
        method: 'POST',
        body: { song_id: songId }
    }),

    // 修改歌曲信息
    adminUpdateSong: (songData) => apiRequest('/Administrator/song/admin_update_song/', {
        method: 'POST',
        body: songData
    }),

    // 查看系统日志
    getSystemLogs: (filters = {}) => apiRequest('/Administrator/get_system_logs/', {
        method: 'POST',
        body: filters
    }),

    // 获取用户行为统计
    getUserBehaviorStats: (filters = {}) => apiRequest('/Administrator/user/get_user_behavior_stats/', {
        method: 'POST',
        body: filters
    }),

    // 获取特定用户的详细行为统计
    getSpecificUserStats: (targetUserId, filters = {}) => apiRequest('/Administrator/user/get_specific_user_stats/', {
        method: 'POST',
        body: { target_user_id: targetUserId, ...filters }
    }),

    // 获取待审核评论列表
    getPendingComments: (page = 1, pageSize = 20) => apiRequest('/Administrator/comment/admin_get_pending_comments/', {
        method: 'POST',
        body: { page, page_size: pageSize }
    }),

    // 管理员审核评论
    auditComment: (commentId, result, banUser = false) => apiRequest('/Administrator/comment/admin_audit_comment/', {
        method: 'POST',
        body: { comment_id: commentId, result, ban_user: banUser }
    })
};

// ====================================
// 辅助函数
// ====================================

// 显示消息提示
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// 检查登录状态
function checkLogin() {
    if (!UserStore.isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// 更新导航栏用户信息
function updateNavbar() {
    const userInfoEl = document.querySelector('.user-info');
    if (userInfoEl && UserStore.isLoggedIn()) {
        userInfoEl.innerHTML = `
            <span>欢迎，${UserStore.getUsername()}</span>
            <button class="logout-btn" onclick="handleLogout()">退出登录</button>
        `;
    }
}

// 处理登出
async function handleLogout() {
    try {
        await UserAPI.logout();
    } catch (error) {
        console.log('Logout error:', error);
    }
    UserStore.clearUser();
    window.location.href = 'login.html';
}

// 格式化时间
function formatDuration(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${min}:${sec.toString().padStart(2, '0')}`;
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ====================================
// 通用UI工具函数
// ====================================

// 显示加载状态
function showLoading(containerId, message = '加载中...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

// 显示错误信息
function showError(containerId, message, canRetry = false, retryCallback = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const retryButton = canRetry && retryCallback ? 
        `<button class="btn btn-secondary" onclick="${retryCallback}">重试</button>` : '';
    
    container.innerHTML = `
        <div class="alert alert-error">
            <p>${message}</p>
            ${retryButton}
        </div>
    `;
}

// 显示空状态
function showEmpty(containerId, message = '暂无数据') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="empty-state">
            <p>${message}</p>
        </div>
    `;
}

// 带错误处理的API请求包装器
async function safeApiRequest(apiCall, containerId, loadingMessage = '加载中...', errorMessage = '加载失败', canRetry = false, retryCallback = null) {
    try {
        showLoading(containerId, loadingMessage);
        const result = await apiCall();
        return result;
    } catch (error) {
        console.error('API请求错误:', error);
        const errorMsg = error.error || error.message || errorMessage;
        showError(containerId, errorMsg, canRetry, retryCallback);
        throw error;
    }
}

// 简单的数据缓存
const DataCache = {
    cache: {},
    ttl: 5 * 60 * 1000, // 5分钟缓存
    
    set(key, data) {
        this.cache[key] = {
            data,
            timestamp: Date.now()
        };
    },
    
    get(key) {
        const item = this.cache[key];
        if (!item) return null;
        
        // 检查是否过期
        if (Date.now() - item.timestamp > this.ttl) {
            delete this.cache[key];
            return null;
        }
        
        return item.data;
    },
    
    clear() {
        this.cache = {};
    },
    
    // 带缓存的API请求
    async cachedRequest(cacheKey, apiCall, containerId, loadingMessage = '加载中...', errorMessage = '加载失败') {
        console.log('DataCache.cachedRequest调用:', cacheKey, containerId);
        
        // 尝试从缓存获取数据
        const cachedData = this.get(cacheKey);
        if (cachedData) {
            console.log('从缓存获取数据:', cacheKey);
            return cachedData;
        }
        
        // 缓存中没有数据，发起API请求
        try {
            console.log('发起API请求:', cacheKey);
            if (containerId) {
                showLoading(containerId, loadingMessage);
            }
            const result = await apiCall();
            console.log('API请求成功:', cacheKey, result);
            return result;
        } catch (error) {
            console.error('API请求错误:', error);
            if (containerId) {
                let errorMsg = errorMessage;
                if (error.error) {
                    errorMsg = error.error;
                } else if (error.message) {
                    errorMsg = error.message;
                }
                
                // 如果有原始响应，尝试提取有用的信息
                if (error.rawResponse && error.rawResponse.includes('<')) {
                    errorMsg = '服务器返回了错误页面，请检查API端点是否正确';
                }
                
                showError(containerId, errorMsg, false, null);
            }
            throw error;
        }
    }
};
