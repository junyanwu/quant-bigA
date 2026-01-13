# 配置文件
import os
from datetime import datetime

# 数据配置
DATA_CONFIG = {
    'data_path': './data',
    'start_date': '2015-01-01',  # 从2015年开始，数据更完整
    'end_date': datetime.now().strftime('%Y-%m-%d'),
    'symbols_file': './config/symbols.json',
    'max_workers': 10,           # 并行下载线程数
    'retry_times': 3,            # 重试次数
    'batch_size': 100            # 批量下载大小
}

# 策略配置
STRATEGY_CONFIG = {
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'position_ratio': 0.95,  # 仓位比例
    'stop_loss': 0.05,       # 止损比例
    'take_profit': 0.10      # 止盈比例
}

# 回测配置
BACKTEST_CONFIG = {
    'initial_capital': 1000000,  # 初始资金
    'commission': 0.0003,        # 手续费
    'slippage': 0.001,           # 滑点
    'benchmark': '000300.SH'     # 基准指数（沪深300）
}

# 数据源配置
DATA_SOURCE_CONFIG = {
    'akshare': {
        'enabled': True,
        'timeout': 30
    },
    'qmt': {
        'enabled': True,
        'account': '',
        'password': ''
    }
}