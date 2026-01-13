/* A股量化交易系统 - 主JavaScript文件 */

// 全局变量
let socket = null;
let currentPage = '';

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

// 初始化应用
function initializeApplication() {
    // 初始化Socket.io连接
    initializeSocketIO();
    
    // 设置当前页面
    currentPage = window.location.pathname;
    
    // 更新页面特定功能
    updatePageSpecificFeatures();
    
    // 设置自动刷新（如果需要）
    setupAutoRefresh();
    
    // 绑定全局事件
    bindGlobalEvents();
}

// 初始化Socket.io连接
function initializeSocketIO() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('WebSocket连接成功');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            console.log('WebSocket连接断开');
            updateConnectionStatus(false);
        });
        
        socket.on('system_info', function(data) {
            updateSystemInfo(data);
        });
        
        socket.on('download_progress', function(data) {
            updateDownloadProgress(data);
        });
        
        socket.on('download_complete', function(data) {
            handleDownloadComplete(data);
        });
        
        socket.on('download_error', function(data) {
            handleDownloadError(data);
        });
        
        socket.on('backtest_progress', function(data) {
            updateBacktestProgress(data);
        });
        
        socket.on('backtest_complete', function(data) {
            handleBacktestComplete(data);
        });
        
    } catch (error) {
        console.error('Socket.io初始化失败:', error);
    }
}

// 更新连接状态
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.innerHTML = connected ? 
            '<span class="status-indicator status-online"></span>在线' : 
            '<span class="status-indicator status-offline"></span>离线';
    }
}

// 更新系统信息
function updateSystemInfo(data) {
    // 更新首页统计数据
    if (document.getElementById('stocks-count')) {
        document.getElementById('stocks-count').textContent = data.stocks_count + ' 只';
    }
    if (document.getElementById('etfs-count')) {
        document.getElementById('etfs-count').textContent = data.etfs_count + ' 只';
    }
    if (document.getElementById('last-update')) {
        document.getElementById('last-update').textContent = data.last_update;
    }
}

// 更新下载进度
function updateDownloadProgress(data) {
    const progressBar = document.getElementById('downloadProgress');
    const currentElement = document.getElementById('downloadCurrent');
    const totalElement = document.getElementById('downloadTotal');
    
    if (progressBar) {
        const percentage = Math.round(data.percentage);
        progressBar.style.width = percentage + '%';
        progressBar.textContent = percentage + '%';
    }
    
    if (currentElement) {
        currentElement.textContent = data.current;
    }
    
    if (totalElement) {
        totalElement.textContent = data.total;
    }
}

// 处理下载完成
function handleDownloadComplete(data) {
    // 隐藏下载模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('downloadModal'));
    if (modal) {
        modal.hide();
    }
    
    // 显示成功消息
    showNotification('数据下载完成！', 'success');
    
    // 刷新页面数据
    setTimeout(() => {
        location.reload();
    }, 2000);
}

// 处理下载错误
function handleDownloadError(data) {
    // 隐藏下载模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('downloadModal'));
    if (modal) {
        modal.hide();
    }
    
    // 显示错误消息
    showNotification('下载失败: ' + data.error, 'error');
}

// 更新回测进度
function updateBacktestProgress(data) {
    const progressBar = document.getElementById('backtestProgress');
    const statusElement = document.getElementById('backtestStatus');
    
    if (progressBar) {
        const percentage = Math.round(data.percentage);
        progressBar.style.width = percentage + '%';
        progressBar.textContent = percentage + '%';
    }
    
    if (statusElement) {
        statusElement.textContent = data.status;
    }
}

// 处理回测完成
function handleBacktestComplete(data) {
    // 隐藏回测模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('backtestModal'));
    if (modal) {
        modal.hide();
    }
    
    if (data.error) {
        showNotification('回测失败: ' + data.error, 'error');
    } else {
        showNotification('回测完成！', 'success');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// 更新页面特定功能
function updatePageSpecificFeatures() {
    switch (currentPage) {
        case '/':
            initializeHomePage();
            break;
        case '/dashboard':
            initializeDashboard();
            break;
        case '/data_management':
            initializeDataManagement();
            break;
        case '/dca_backtest':
            initializeDCABacktest();
            break;
        case '/strategy_backtest':
            initializeStrategyBacktest();
            break;
        case '/realtime_monitor':
            initializeRealtimeMonitor();
            break;
    }
}

// 初始化首页
function initializeHomePage() {
    // 请求系统信息
    if (socket && socket.connected) {
        socket.emit('request_system_info');
    }
    
    // 设置时间更新
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
}

// 更新当前时间
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleString('zh-CN');
    }
}

// 设置自动刷新
function setupAutoRefresh() {
    // 只在特定页面设置自动刷新
    if (currentPage === '/realtime_monitor') {
        setInterval(() => {
            if (socket && socket.connected) {
                socket.emit('refresh_data');
            }
        }, 5000); // 每5秒刷新一次
    }
}

// 绑定全局事件
function bindGlobalEvents() {
    // 全局错误处理
    window.addEventListener('error', function(e) {
        console.error('全局错误:', e.error);
        showNotification('发生错误: ' + e.error.message, 'error');
    });
    
    // 网络状态监听
    window.addEventListener('online', function() {
        showNotification('网络连接已恢复', 'success');
        if (socket) {
            socket.connect();
        }
    });
    
    window.addEventListener('offline', function() {
        showNotification('网络连接已断开', 'warning');
    });
}

// 工具函数：格式化数字
function formatNumber(num, decimals = 2) {
    return num.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// 工具函数：格式化百分比
function formatPercent(num, decimals = 2) {
    return (num * 100).toFixed(decimals) + '%';
}

// 工具函数：格式化金额
function formatCurrency(amount) {
    if (Math.abs(amount) >= 100000000) {
        return (amount / 100000000).toFixed(2) + '亿元';
    } else if (Math.abs(amount) >= 10000) {
        return (amount / 10000).toFixed(2) + '万元';
    } else {
        return formatNumber(amount) + '元';
    }
}

// 工具函数：防抖
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

// 工具函数：节流
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 导出全局函数
window.QuantTradingUI = {
    showNotification,
    formatNumber,
    formatPercent,
    formatCurrency,
    debounce,
    throttle
};

// 页面特定初始化函数（需要在各页面中实现）
function initializeDashboard() {
    // 仪表板页面初始化
    console.log('初始化仪表板');
}

function initializeDataManagement() {
    // 数据管理页面初始化
    console.log('初始化数据管理');
}

function initializeDCABacktest() {
    // 定投回测页面初始化
    console.log('初始化定投回测');
}

function initializeStrategyBacktest() {
    // 策略回测页面初始化
    console.log('初始化策略回测');
}

function initializeRealtimeMonitor() {
    // 实时监控页面初始化
    console.log('初始化实时监控');
}