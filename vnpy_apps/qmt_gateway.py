#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易接口 - 基于VeighNa框架
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.constant import Exchange, Direction, Offset, OrderType, Status
from vnpy.trader.object import TickData, OrderData, TradeData, PositionData, AccountData


try:
    from xtquant import xtdata
    from xtquant.xttrader import XtQuantTrader
    from xtquant.xttype import StockAccount
    QMT_AVAILABLE = True
except ImportError:
    QMT_AVAILABLE = False
    print("警告: xtquant库未安装，QMT功能不可用")


class QMTGateway(BaseGateway):
    """
    QMT交易接口
    基于xtquant库实现中信建投QMT交易接口
    """
    
    def __init__(self, event_engine: EventEngine, gateway_name: str = "QMT"):
        """初始化"""
        super().__init__(event_engine, gateway_name)
        
        self.connected = False
        self.trader = None
        self.account = None
        
        # QMT配置
        self.qmt_dir = ""
        self.session_id = "quant_trader"
        self.account_id = ""
    
    def connect(self, setting: dict) -> None:
        """连接QMT"""
        if not QMT_AVAILABLE:
            self.write_log("QMT不可用: xtquant库未安装")
            return
        
        try:
            # 获取配置
            self.qmt_dir = setting.get("qmt_dir", "")
            self.session_id = setting.get("session_id", "quant_trader")
            self.account_id = setting.get("account_id", "")
            
            if not self.qmt_dir:
                self.write_log("QMT目录未配置")
                return
            
            # 创建交易对象
            self.trader = XtQuantTrader(self.qmt_dir, self.session_id)
            
            # 启动交易线程
            self.trader.start()
            
            # 连接交易服务器
            connect_result = self.trader.connect()
            
            if connect_result == 0:
                self.connected = True
                self.write_log("QMT连接成功")
                
                # 订阅账户
                self.subscribe_account()
                
                # 查询账户信息
                self.query_account()
                self.query_position()
                
            else:
                self.write_log(f"QMT连接失败: {connect_result}")
                
        except Exception as e:
            self.write_log(f"QMT连接异常: {e}")
    
    def subscribe_account(self) -> None:
        """订阅账户"""
        if not self.connected:
            return
        
        try:
            # 创建账户对象
            self.account = StockAccount(self.account_id)
            
            # 订阅账户
            subscribe_result = self.trader.subscribe(self.account)
            
            if subscribe_result == 0:
                self.write_log("账户订阅成功")
            else:
                self.write_log(f"账户订阅失败: {subscribe_result}")
                
        except Exception as e:
            self.write_log(f"订阅账户异常: {e}")
    
    def close(self) -> None:
        """关闭连接"""
        if self.trader:
            self.trader.stop()
            self.connected = False
            self.write_log("QMT连接已关闭")
    
    def subscribe(self, req: dict) -> None:
        """订阅行情"""
        if not self.connected:
            return
        
        try:
            symbol = req.get("symbol", "")
            
            if symbol:
                # 订阅行情
                xtdata.subscribe_quote(symbol, period='1d')
                self.write_log(f"已订阅行情: {symbol}")
                
        except Exception as e:
            self.write_log(f"订阅行情异常: {e}")
    
    def send_order(self, req: dict) -> str:
        """发送委托"""
        if not self.connected:
            return ""
        
        try:
            symbol = req.get("symbol", "")
            price = req.get("price", 0.0)
            volume = req.get("volume", 0)
            direction = req.get("direction", Direction.LONG)
            offset = req.get("offset", Offset.OPEN)
            
            if not symbol or volume <= 0:
                self.write_log("委托参数错误")
                return ""
            
            # 构建QMT委托参数
            order_type = 23  # 限价单
            
            if direction == Direction.SHORT:
                # 卖空操作
                pass
            
            # 发送委托
            order_id = self.trader.order_stock(
                self.account, symbol, order_type, volume, price
            )
            
            if order_id:
                self.write_log(f"委托发送成功: {symbol} {direction.value} {volume}@{price}")
                return str(order_id)
            else:
                self.write_log("委托发送失败")
                return ""
                
        except Exception as e:
            self.write_log(f"发送委托异常: {e}")
            return ""
    
    def cancel_order(self, req: dict) -> None:
        """撤销委托"""
        if not self.connected:
            return
        
        try:
            order_id = req.get("order_id", "")
            
            if order_id:
                # 撤销委托
                cancel_result = self.trader.cancel_order_stock(self.account, order_id)
                
                if cancel_result == 0:
                    self.write_log(f"委托撤销成功: {order_id}")
                else:
                    self.write_log(f"委托撤销失败: {cancel_result}")
                    
        except Exception as e:
            self.write_log(f"撤销委托异常: {e}")
    
    def query_account(self) -> None:
        """查询账户资金"""
        if not self.connected:
            return
        
        try:
            # 查询账户资金
            account_info = self.trader.query_stock_asset(self.account)
            
            if account_info:
                # 创建账户数据对象
                account_data = AccountData(
                    accountid=self.account_id,
                    balance=account_info.total_asset,
                    frozen=account_info.frozen_cash,
                    gateway_name=self.gateway_name
                )
                
                # 推送账户数据
                self.on_account(account_data)
                
        except Exception as e:
            self.write_log(f"查询账户异常: {e}")
    
    def query_position(self) -> None:
        """查询持仓"""
        if not self.connected:
            return
        
        try:
            # 查询持仓
            positions = self.trader.query_stock_positions(self.account)
            
            for pos in positions:
                # 创建持仓数据对象
                position_data = PositionData(
                    symbol=pos.stock_code,
                    exchange=Exchange.SSE if pos.stock_code.startswith('6') else Exchange.SZSE,
                    direction=Direction.LONG,
                    volume=pos.volume,
                    frozen=pos.frozen_volume,
                    price=pos.open_price,
                    pnl=pos.profit,
                    gateway_name=self.gateway_name
                )
                
                # 推送持仓数据
                self.on_position(position_data)
                
        except Exception as e:
            self.write_log(f"查询持仓异常: {e}")
    
    def on_tick(self, tick: TickData) -> None:
        """行情推送回调"""
        # 推送行情数据到事件引擎
        self.event_engine.put(tick)
    
    def on_order(self, order: OrderData) -> None:
        """委托推送回调"""
        # 推送委托数据到事件引擎
        self.event_engine.put(order)
    
    def on_trade(self, trade: TradeData) -> None:
        """成交推送回调"""
        # 推送成交数据到事件引擎
        self.event_engine.put(trade)
    
    def on_account(self, account: AccountData) -> None:
        """账户推送回调"""
        # 推送账户数据到事件引擎
        self.event_engine.put(account)
    
    def on_position(self, position: PositionData) -> None:
        """持仓推送回调"""
        # 推送持仓数据到事件引擎
        self.event_engine.put(position)
    
    def write_log(self, msg: str) -> None:
        """写日志"""
        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(log_msg)
        
        # 推送日志事件
        log_event = Event(
            type="eLog",
            data={
                "gateway_name": self.gateway_name,
                "msg": msg
            }
        )
        self.event_engine.put(log_event)


def get_default_setting() -> Dict[str, any]:
    """获取默认配置"""
    return {
        "qmt_dir": "",
        "session_id": "quant_trader",
        "account_id": ""
    }