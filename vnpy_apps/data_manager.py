#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理应用 - 基于VeighNa框架
"""

import pandas as pd
import akshare as ak
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import HistoryRequest, BarData, TickData
from vnpy.trader.database import BaseDatabase, get_database
from vnpy.trader.datafeed import BaseDatafeed, get_datafeed


class DataManagerApp:
    """
    数据管理应用
    负责获取和管理A股股票、ETF的历史数据
    """
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """初始化"""
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.database = get_database()
        self.datafeed = get_datafeed()
        
        # 数据目录
        self.data_path = "./data"
        os.makedirs(self.data_path, exist_ok=True)
        
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 上海交易所股票
            sh_stocks = ak.stock_info_sh_name_code(symbol="主板A股")
            sh_stocks['exchange'] = Exchange.SSE.value
            
            # 深圳交易所股票  
            sz_stocks = ak.stock_info_sz_name_code(symbol="A股列表")
            sz_stocks['exchange'] = Exchange.SZSE.value
            
            # 合并
            all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
            all_stocks['symbol'] = all_stocks['代码'] + '.' + all_stocks['exchange']
            
            return all_stocks
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_etf_list(self) -> pd.DataFrame:
        """获取ETF列表"""
        try:
            etf_list = ak.fund_etf_spot_em()
            etf_list['exchange'] = etf_list['代码'].apply(
                lambda x: Exchange.SSE.value if x.startswith('51') else Exchange.SZSE.value
            )
            etf_list['symbol'] = etf_list['代码'] + '.' + etf_list['exchange']
            
            return etf_list
        except Exception as e:
            print(f"获取ETF列表失败: {e}")
            return pd.DataFrame()
    
    def download_historical_data(self, symbol: str, exchange: Exchange, 
                                start: str, end: str, interval: Interval = Interval.DAILY) -> List[BarData]:
        """下载历史数据"""
        try:
            # 创建历史数据请求
            req = HistoryRequest(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=datetime.strptime(start, "%Y-%m-%d"),
                end=datetime.strptime(end, "%Y-%m-%d")
            )
            
            # 从数据源获取数据
            bars = self.datafeed.query_bar_history(req)
            
            # 保存到数据库
            if bars:
                self.database.save_bar_data(bars)
            
            return bars
            
        except Exception as e:
            print(f"下载 {symbol} 数据失败: {e}")
            return []
    
    def batch_download_data(self, symbols: List[str], start: str, end: str, 
                           interval: Interval = Interval.DAILY, max_workers: int = 5):
        """批量下载数据"""
        from concurrent.futures import ThreadPoolExecutor
        
        results = {'success': [], 'failed': []}
        
        def download_symbol(symbol_info):
            symbol, exchange_str = symbol_info
            exchange = Exchange(exchange_str)
            
            try:
                bars = self.download_historical_data(symbol, exchange, start, end, interval)
                if bars:
                    results['success'].append(symbol)
                    print(f"成功下载 {symbol} 数据，共 {len(bars)} 条")
                    return True
                else:
                    results['failed'].append(symbol)
                    return False
            except Exception as e:
                results['failed'].append(symbol)
                print(f"下载 {symbol} 失败: {e}")
                return False
        
        # 准备下载任务
        tasks = []
        for symbol in symbols:
            if '.' in symbol:
                sym, exch = symbol.split('.')
                tasks.append((sym, exch))
        
        # 并行下载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(download_symbol, tasks))
        
        # 保存结果
        with open(f"{self.data_path}/download_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    def load_bar_data(self, symbol: str, exchange: Exchange, 
                     start: datetime, end: datetime, interval: Interval) -> List[BarData]:
        """从数据库加载K线数据"""
        try:
            bars = self.database.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=start,
                end=end
            )
            return bars
        except Exception as e:
            print(f"加载 {symbol} 数据失败: {e}")
            return []
    
    def get_available_symbols(self) -> Dict[str, List[str]]:
        """获取本地可用的标的"""
        # 这里可以查询数据库中有数据的标的
        # 简化实现：返回空字典，实际应该查询数据库
        return {'stocks': [], 'etfs': [], 'index': []}


class DataManagerWidget(QtWidgets.QWidget):
    """数据管理界面"""
    
    def __init__(self, data_manager: DataManagerApp):
        super().__init__()
        
        self.data_manager = data_manager
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("数据管理器")
        self.setFixedSize(800, 600)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout()
        
        # 数据下载区域
        download_group = QtWidgets.QGroupBox("数据下载")
        download_layout = QtWidgets.QFormLayout()
        
        self.start_date_edit = QtWidgets.QDateEdit()
        self.end_date_edit = QtWidgets.QDateEdit()
        self.interval_combo = QtWidgets.QComboBox()
        self.download_btn = QtWidgets.QPushButton("开始下载")
        
        download_layout.addRow("开始日期:", self.start_date_edit)
        download_layout.addRow("结束日期:", self.end_date_edit)
        download_layout.addRow("周期:", self.interval_combo)
        download_layout.addRow(self.download_btn)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # 日志区域
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
        # 连接信号
        self.download_btn.clicked.connect(self.on_download_clicked)
    
    def on_download_clicked(self):
        """下载按钮点击事件"""
        self.log_text.append("开始下载数据...")
        
        # 获取股票和ETF列表
        stocks = self.data_manager.get_stock_list()
        etfs = self.data_manager.get_etf_list()
        
        all_symbols = list(stocks['symbol']) + list(etfs['symbol'])
        
        # 批量下载
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        results = self.data_manager.batch_download_data(all_symbols, start_date, end_date)
        
        self.log_text.append(f"下载完成！成功: {len(results['success'])}, 失败: {len(results['failed'])}")