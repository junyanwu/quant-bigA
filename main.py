#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股量化交易主程序 - 基于VeighNa和QMT
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, List

# VeighNa框架导入
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.gateway.ctp import CtpGateway
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.data_recorder import DataRecorderApp
from vnpy.app.algo_trading import AlgoTradingApp
from vnpy.app.risk_manager import RiskManagerApp
from vnpy.app.spread_trading import SpreadTradingApp

# 自定义应用模块
from vnpy_apps.data_manager import DataManagerApp, DataManagerWidget
from vnpy_apps.macd_strategy import MACDStrategyApp, MACDStrategyWidget
from vnpy_apps.qmt_gateway import QMTGateway

# 导入配置
from config.config import DATA_CONFIG, STRATEGY_CONFIG, BACKTEST_CONFIG, DATA_SOURCE_CONFIG


class QuantTrader:
    """
    量化交易主程序
    基于VeighNa框架构建完整的量化交易系统
    """
    
    def __init__(self):
        """初始化"""
        # 创建事件引擎
        self.event_engine = EventEngine()
        
        # 创建主引擎
        self.main_engine = MainEngine(self.event_engine)
        
        # 加载配置
        self.load_config()
        
        # 初始化应用模块
        self.init_apps()
        
        # 初始化界面
        self.main_window = None
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = "config/vnpy_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
                print("配置文件不存在，使用默认配置")
                
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.config = {}
    
    def init_apps(self):
        """初始化应用模块"""
        try:
            # 添加标准VeighNa应用
            self.main_engine.add_app(CtaStrategyApp)
            self.main_engine.add_app(CtaBacktesterApp)
            self.main_engine.add_app(DataRecorderApp)
            self.main_engine.add_app(AlgoTradingApp)
            self.main_engine.add_app(RiskManagerApp)
            self.main_engine.add_app(SpreadTradingApp)
            
            # 添加自定义应用
            self.data_manager = DataManagerApp(self.main_engine, self.event_engine)
            self.macd_strategy = MACDStrategyApp(self.main_engine, self.event_engine)
            
            # 添加QMT交易接口
            if DATA_SOURCE_CONFIG.get('qmt', {}).get('enabled'):
                self.main_engine.add_gateway(QMTGateway)
            
            print("应用模块初始化完成")
            
        except Exception as e:
            print(f"初始化应用模块失败: {e}")
    
    def run_gui(self):
        """运行图形界面"""
        try:
            # 创建Qt应用
            qapp = create_qapp()
            
            # 创建主窗口
            self.main_window = MainWindow(self.main_engine, self.event_engine)
            
            # 添加自定义组件到主窗口
            self.add_custom_widgets()
            
            # 显示主窗口
            self.main_window.showMaximized()
            
            # 运行应用
            qapp.exec()
            
        except Exception as e:
            print(f"运行图形界面失败: {e}")
    
    def add_custom_widgets(self):
        """添加自定义组件到主窗口"""
        try:
            # 创建自定义组件
            data_widget = DataManagerWidget(self.data_manager)
            strategy_widget = MACDStrategyWidget(self.macd_strategy)
            
            # 添加到主窗口
            self.main_window.add_widget(data_widget, "数据管理器")
            self.main_window.add_widget(strategy_widget, "MACD策略")
            
        except Exception as e:
            print(f"添加自定义组件失败: {e}")
    
    def download_data(self):
        """下载A股数据"""
        try:
            print("开始下载A股数据...")
            
            # 获取股票和ETF列表
            stocks = self.data_manager.get_stock_list()
            etfs = self.data_manager.get_etf_list()
            
            all_symbols = list(stocks['symbol']) + list(etfs['symbol'])
            
            # 批量下载数据
            start_date = DATA_CONFIG.get('start_date', '2020-01-01')
            end_date = DATA_CONFIG.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            
            results = self.data_manager.batch_download_data(
                all_symbols, start_date, end_date, max_workers=5
            )
            
            print(f"数据下载完成！成功: {len(results['success'])}, 失败: {len(results['failed'])}")
            
            # 保存下载结果
            with open('data/download_summary.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            return results
            
        except Exception as e:
            print(f"下载数据失败: {e}")
            return {}
    
    def run_backtest(self, symbol: str = "000001.SH", start_date: str = "2020-01-01", 
                    end_date: str = "2024-12-31"):
        """运行回测"""
        try:
            from backtesting.backtest_engine import BacktestEngine
            
            print(f"开始回测: {symbol} {start_date} 至 {end_date}")
            
            # 创建回测引擎
            backtest_engine = BacktestEngine(self.main_engine)
            
            # 运行回测
            performance = backtest_engine.run_backtest(
                strategy_name="MACD_Strategy",
                vt_symbol=symbol,
                interval=Interval.DAILY,
                start=datetime.strptime(start_date, "%Y-%m-%d"),
                end=datetime.strptime(end_date, "%Y-%m-%d"),
                rate=BACKTEST_CONFIG.get('commission', 0.0003),
                slippage=BACKTEST_CONFIG.get('slippage', 0.001),
                capital=BACKTEST_CONFIG.get('initial_capital', 1000000)
            )
            
            # 生成报告
            report = backtest_engine.generate_report("MACD_Strategy")
            print(report)
            
            # 绘制图表
            backtest_engine.plot_performance("MACD_Strategy", "backtest_results.png")
            
            # 保存结果
            backtest_engine.save_results("backtest_results.json")
            
            return performance
            
        except Exception as e:
            print(f"运行回测失败: {e}")
            return {}
    
    def run_live_trading(self):
        """运行实盘交易"""
        try:
            print("启动实盘交易...")
            
            # 连接交易接口
            if DATA_SOURCE_CONFIG.get('qmt', {}).get('enabled'):
                qmt_setting = {
                    "qmt_dir": DATA_SOURCE_CONFIG['qmt'].get('qmt_dir', ''),
                    "session_id": DATA_SOURCE_CONFIG['qmt'].get('session_id', 'quant_trader'),
                    "account_id": DATA_SOURCE_CONFIG['qmt'].get('account_id', '')
                }
                
                # 连接QMT
                self.main_engine.connect(qmt_setting, "QMT")
            
            # 添加MACD策略
            strategy_setting = {
                "fast_period": STRATEGY_CONFIG.get('macd_fast', 12),
                "slow_period": STRATEGY_CONFIG.get('macd_slow', 26),
                "signal_period": STRATEGY_CONFIG.get('macd_signal', 9),
                "fixed_size": 100,
                "stop_loss": STRATEGY_CONFIG.get('stop_loss', 0.05),
                "take_profit": STRATEGY_CONFIG.get('take_profit', 0.10)
            }
            
            # 添加策略到监控的标的
            symbols = ["000001.SH", "000300.SH"]  # 示例标的
            
            for symbol in symbols:
                strategy_name = f"MACD_{symbol}"
                self.macd_strategy.add_strategy(strategy_name, symbol, strategy_setting)
                self.macd_strategy.init_strategy(strategy_name)
                self.macd_strategy.start_strategy(strategy_name)
                print(f"策略 {strategy_name} 已启动")
            
            print("实盘交易已启动")
            
        except Exception as e:
            print(f"启动实盘交易失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="A股量化交易系统")
    parser.add_argument('--mode', choices=['gui', 'download', 'backtest', 'live'], 
                       default='gui', help='运行模式')
    parser.add_argument('--symbol', default='000001.SH', help='回测标的')
    parser.add_argument('--start', default='2020-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    
    args = parser.parse_args()
    
    # 创建量化交易程序
    trader = QuantTrader()
    
    if args.mode == 'gui':
        # 图形界面模式
        trader.run_gui()
    
    elif args.mode == 'download':
        # 数据下载模式
        trader.download_data()
    
    elif args.mode == 'backtest':
        # 回测模式
        trader.run_backtest(args.symbol, args.start, args.end)
    
    elif args.mode == 'live':
        # 实盘交易模式
        trader.run_live_trading()
    
    else:
        print("未知的运行模式")


if __name__ == "__main__":
    main()