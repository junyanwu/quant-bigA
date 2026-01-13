#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD策略应用 - 基于VeighNa CTA策略框架
"""

import talib
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.constant import Direction, Offset, Interval
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.app.cta_strategy import (
    CtaTemplate, 
    CtaEngine, 
    StopOrder, 
    TickData, 
    BarData,
    OrderData
)


class MACDStrategy(CtaTemplate):
    """
    MACD金叉死叉策略
    基于VeighNa CTA策略模板实现
    """
    
    author = "Quant Trader"
    
    # 策略参数
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    # 风险控制参数
    fixed_size = 100
    stop_loss = 0.05
    take_profit = 0.10
    
    # 策略变量
    macd_value = 0.0
    macd_signal = 0.0
    macd_hist = 0.0
    
    # 交易状态
    long_entry = 0.0
    short_entry = 0.0
    
    parameters = ["fast_period", "slow_period", "signal_period", "fixed_size", "stop_loss", "take_profit"]
    variables = ["macd_value", "macd_signal", "macd_hist", "long_entry", "short_entry"]
    
    def __init__(self, cta_engine: CtaEngine, strategy_name: str, vt_symbol: str, setting: dict):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 创建K线合成器
        self.bg = BarGenerator(self.on_bar)
        
        # 创建数组管理器
        self.am = ArrayManager()
        
        # 初始化指标
        self.macd_value = 0.0
        self.macd_signal = 0.0
        self.macd_hist = 0.0
    
    def on_init(self):
        """策略初始化"""
        self.write_log("MACD策略初始化")
        self.load_bar(10)
    
    def on_start(self):
        """策略启动"""
        self.write_log("MACD策略启动")
    
    def on_stop(self):
        """策略停止"""
        self.write_log("MACD策略停止")
    
    def on_tick(self, tick: TickData):
        """Tick数据推送"""
        self.bg.update_tick(tick)
    
    def on_bar(self, bar: BarData):
        """K线数据推送"""
        # 更新数组管理器
        self.am.update_bar(bar)
        
        if not self.am.inited:
            return
        
        # 计算MACD指标
        self.calculate_macd()
        
        # 生成交易信号
        self.generate_signal(bar)
    
    def calculate_macd(self):
        """计算MACD指标"""
        if len(self.am.close) < self.slow_period:
            return
        
        try:
            # 使用TA-Lib计算MACD
            macd, macd_signal, macd_hist = talib.MACD(
                self.am.close,
                fastperiod=self.fast_period,
                slowperiod=self.slow_period,
                signalperiod=self.signal_period
            )
            
            self.macd_value = macd[-1] if not np.isnan(macd[-1]) else 0.0
            self.macd_signal = macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0.0
            self.macd_hist = macd_hist[-1] if not np.isnan(macd_hist[-1]) else 0.0
            
        except Exception as e:
            self.write_log(f"计算MACD指标失败: {e}")
    
    def generate_signal(self, bar: BarData):
        """生成交易信号"""
        if self.macd_value == 0 or self.macd_signal == 0:
            return
        
        # 计算前一个周期的MACD值
        if len(self.am.close) < self.slow_period + 1:
            return
        
        try:
            # 计算前一个周期的MACD
            prev_macd, prev_signal, _ = talib.MACD(
                self.am.close[:-1],
                fastperiod=self.fast_period,
                slowperiod=self.slow_period,
                signalperiod=self.signal_period
            )
            
            prev_macd_val = prev_macd[-1] if len(prev_macd) > 0 and not np.isnan(prev_macd[-1]) else 0.0
            prev_signal_val = prev_signal[-1] if len(prev_signal) > 0 and not np.isnan(prev_signal[-1]) else 0.0
            
            # 金叉判断：当前MACD上穿信号线，且前一个周期MACD在信号线下方
            golden_cross = (self.macd_value > self.macd_signal and 
                          prev_macd_val <= prev_signal_val)
            
            # 死叉判断：当前MACD下穿信号线，且前一个周期MACD在信号线上方
            death_cross = (self.macd_value < self.macd_signal and 
                         prev_macd_val >= prev_signal_val)
            
            # 执行交易逻辑
            if golden_cross and self.pos == 0:
                # 金叉买入
                self.buy(bar.close_price, self.fixed_size)
                self.long_entry = bar.close_price
                self.write_log(f"金叉买入信号: {bar.close_price}")
            
            elif death_cross and self.pos > 0:
                # 死叉卖出
                self.sell(bar.close_price, abs(self.pos))
                self.write_log(f"死叉卖出信号: {bar.close_price}")
            
            # 止损止盈逻辑
            elif self.pos > 0:
                # 多头止损
                if bar.close_price <= self.long_entry * (1 - self.stop_loss):
                    self.sell(bar.close_price, abs(self.pos))
                    self.write_log(f"多头止损: {bar.close_price}")
                
                # 多头止盈
                elif bar.close_price >= self.long_entry * (1 + self.take_profit):
                    self.sell(bar.close_price, abs(self.pos))
                    self.write_log(f"多头止盈: {bar.close_price}")
            
            # 更新界面显示
            self.put_event()
            
        except Exception as e:
            self.write_log(f"生成交易信号失败: {e}")
    
    def on_order(self, order: OrderData):
        """委托推送"""
        pass
    
    def on_trade(self, trade: TradeData):
        """成交推送"""
        # 更新持仓成本
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
        
        self.put_event()
    
    def on_stop_order(self, stop_order: StopOrder):
        """停止单推送"""
        pass


class MACDStrategyApp:
    """
    MACD策略应用
    管理MACD策略的配置和运行
    """
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """初始化"""
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cta_engine = main_engine.get_engine("CtaStrategy")
        
        # 策略配置
        self.strategy_settings = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "fixed_size": 100,
            "stop_loss": 0.05,
            "take_profit": 0.10
        }
    
    def add_strategy(self, strategy_name: str, vt_symbol: str, setting: dict = None):
        """添加策略"""
        if not setting:
            setting = self.strategy_settings
        
        try:
            # 添加策略到CTA引擎
            self.cta_engine.add_strategy(
                class_name="MACDStrategy",
                strategy_name=strategy_name,
                vt_symbol=vt_symbol,
                setting=setting
            )
            
            return True
        except Exception as e:
            print(f"添加策略失败: {e}")
            return False
    
    def init_strategy(self, strategy_name: str):
        """初始化策略"""
        try:
            self.cta_engine.init_strategy(strategy_name)
            return True
        except Exception as e:
            print(f"初始化策略失败: {e}")
            return False
    
    def start_strategy(self, strategy_name: str):
        """启动策略"""
        try:
            self.cta_engine.start_strategy(strategy_name)
            return True
        except Exception as e:
            print(f"启动策略失败: {e}")
            return False
    
    def stop_strategy(self, strategy_name: str):
        """停止策略"""
        try:
            self.cta_engine.stop_strategy(strategy_name)
            return True
        except Exception as e:
            print(f"停止策略失败: {e}")
            return False
    
    def get_strategy_status(self, strategy_name: str) -> Dict:
        """获取策略状态"""
        try:
            strategy = self.cta_engine.strategies.get(strategy_name)
            if strategy:
                return {
                    "name": strategy_name,
                    "inited": strategy.inited,
                    "trading": strategy.trading,
                    "pos": strategy.pos,
                    "macd_value": getattr(strategy, 'macd_value', 0),
                    "macd_signal": getattr(strategy, 'macd_signal', 0),
                    "macd_hist": getattr(strategy, 'macd_hist', 0)
                }
            else:
                return {}
        except Exception as e:
            print(f"获取策略状态失败: {e}")
            return {}


class MACDStrategyWidget(QtWidgets.QWidget):
    """MACD策略界面"""
    
    def __init__(self, strategy_app: MACDStrategyApp):
        super().__init__()
        
        self.strategy_app = strategy_app
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("MACD策略管理器")
        self.setFixedSize(600, 400)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout()
        
        # 策略配置区域
        config_group = QtWidgets.QGroupBox("策略配置")
        config_layout = QtWidgets.QFormLayout()
        
        self.fast_period_spin = QtWidgets.QSpinBox()
        self.slow_period_spin = QtWidgets.QSpinBox()
        self.signal_period_spin = QtWidgets.QSpinBox()
        self.fixed_size_spin = QtWidgets.QSpinBox()
        
        config_layout.addRow("快线周期:", self.fast_period_spin)
        config_layout.addRow("慢线周期:", self.slow_period_spin)
        config_layout.addRow("信号周期:", self.signal_period_spin)
        config_layout.addRow("固定手数:", self.fixed_size_spin)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 策略控制区域
        control_group = QtWidgets.QGroupBox("策略控制")
        control_layout = QtWidgets.QHBoxLayout()
        
        self.init_btn = QtWidgets.QPushButton("初始化")
        self.start_btn = QtWidgets.QPushButton("启动")
        self.stop_btn = QtWidgets.QPushButton("停止")
        
        control_layout.addWidget(self.init_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 状态显示区域
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)
        
        # 连接信号
        self.init_btn.clicked.connect(self.on_init_clicked)
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
    
    def on_init_clicked(self):
        """初始化按钮点击"""
        self.status_text.append("初始化策略...")
    
    def on_start_clicked(self):
        """启动按钮点击"""
        self.status_text.append("启动策略...")
    
    def on_stop_clicked(self):
        """停止按钮点击"""
        self.status_text.append("停止策略...")