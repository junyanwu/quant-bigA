#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯定投策略
基于VeighNa框架的定投策略

策略特点：
1. 纯定投，不做T
2. 每周定投固定金额
3. 达到止盈条件时卖出全部仓位
4. 卖出后继续定投
"""

import pandas as pd
from typing import Dict
from datetime import datetime
import json
import os

from strategies.indicators import calculate_all_indicators
from strategies.base_strategy import BaseStrategy


class DcaOnlyStrategy(BaseStrategy):
    """
    纯定投策略
    
    策略组成：
    1. 定投部分：每周固定金额定投
    2. 止盈部分：达到20%收益且价格低于MA10时卖出全部仓位
    3. 继续定投：卖出后继续按计划定投
    
    策略思路：
    - 定投：不择时，每周定投固定金额
    - 止盈：收益达到20%且价格跌破MA10时卖出全部
    - 循环：卖出后继续定投，形成完整投资周期
    """
    
    def __init__(self, 
                 total_capital: float = 500000.0,
                 dca_amount_per_week: float = 500.0,
                 profit_target: float = 0.20,
                 commission: float = 0.0003,
                 slippage: float = 0.001):
        """
        初始化策略参数
        
        参数：
        - 总资金：默认50万元
        - 每周定投金额：默认500元
        - 止盈目标：默认20%
        - 手续费：默认0.03%
        - 滑点：默认0.1%
        
        策略思路：
        - 定投：每周第一个交易日定投固定金额
        - 止盈：收益达到目标且价格跌破MA10时卖出全部
        - 循环：卖出后继续定投
        
        Args:
            total_capital: 总资金
            dca_amount_per_week: 每周定投金额
            profit_target: 止盈目标（收益率）
            commission: 手续费率
            slippage: 滑点率
        """
        self.total_capital = total_capital
        self.dca_amount_per_week = dca_amount_per_week
        self.profit_target = profit_target
        self.commission = commission
        self.slippage = slippage
        
        super().__init__()
        
        self.cash = total_capital
        self.dca_cash = total_capital
        
        self.params = {
            'total_capital': total_capital,
            'dca_amount_per_week': dca_amount_per_week,
            'profit_target': profit_target,
            'commission': commission,
            'slippage': slippage,
            'version': '1.0'
        }
    
    def on_bar(self, bar_data: Dict, date: datetime):
        """
        每个bar的回调函数
        
        Args:
            bar_data: 包含OHLCV和技术指标的数据
            date: 当前日期
        """
        symbol = bar_data.get('symbol', '')
        
        if symbol not in self.dca_positions:
            self.dca_positions[symbol] = {'shares': 0.0, 'cost': 0.0, 'avg_price': 0.0}
        
        self._execute_dca_logic(bar_data, date, symbol)
        self._record_daily_nav(bar_data, date, symbol)
    
    def _execute_dca_logic(self, bar_data: Dict, date: datetime, symbol: str):
        """
        执行定投逻辑
        
        策略逻辑：
        1. 每周第一个交易日定投
        2. 计算当前收益率
        3. 达到止盈条件且价格低于MA10时卖出全部
        """
        price = bar_data['close']
        position = self.dca_positions[symbol]
        ma10 = bar_data.get('ma10', 0)
        
        profit_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            profit_ratio = (current_value - position['cost']) / position['cost']
        
        is_first_day_of_week = date.weekday() == 0
        
        if is_first_day_of_week and self.dca_cash >= self.dca_amount_per_week:
            shares = self._calculate_shares(self.dca_amount_per_week, price)
            if shares > 0:
                self._buy_dca(symbol, shares, price, date)
        
        should_sell = (
            position['shares'] > 0 and
            profit_ratio >= self.profit_target and
            price < ma10
        )
        
        if should_sell:
            sell_shares = position['shares']
            if sell_shares > 0:
                self._sell_dca(symbol, sell_shares, price, date)
    
    def _buy_dca(self, symbol: str, shares: float, price: float, date: datetime):
        """
        定投买入
        
        Args:
            symbol: 标的代码
            shares: 买入股数
            price: 价格
            date: 日期
        """
        self._execute_buy(self.dca_positions, self.dca_cash, symbol, shares, price, date, 'dca')
    
    def _sell_dca(self, symbol: str, shares: float, price: float, date: datetime):
        """
        定投卖出
        
        Args:
            symbol: 标的代码
            shares: 卖出股数
            price: 价格
            date: 日期
        """
        self._execute_sell(self.dca_positions, self.dca_cash, symbol, shares, price, date, 'dca')
    
    def _calculate_shares(self, amount: float, price: float) -> float:
        """
        计算可买入股数
        
        Args:
            amount: 买入金额
            price: 价格
            
        Returns:
            可买入股数
        """
        commission = self._calculate_commission(amount)
        total_cost = amount + commission
        shares = int(total_cost / (price * (1 + self.slippage)))
        return max(shares, 0)
    
    def get_results(self) -> Dict:
        """
        获取策略结果
        
        Returns:
            包含策略结果的字典
        """
        if not self.daily_nav:
            return {
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'final_value': 0,
                'dca_buy_count': 0,
                'dca_sell_count': 0,
                't_buy_count': 0,
                't_sell_count': 0,
                't_profit': 0,
                'data_start_date': '',
                'data_end_date': '',
                'annual_returns': []
            }
        
        final_nav = self.daily_nav[-1]
        initial_nav = self.daily_nav[0]
        
        total_return = final_nav['total_return']
        
        data_start_date = self.daily_nav[0]['date'].strftime('%Y-%m-%d')
        data_end_date = self.daily_nav[-1]['date'].strftime('%Y-%m-%d')
        
        days = (self.daily_nav[-1]['date'] - self.daily_nav[0]['date']).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0
        
        max_drawdown = self._calculate_max_drawdown()
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        dca_buy_count = len([t for t in self.dca_trades if t['type'] == 'buy'])
        dca_sell_count = len([t for t in self.dca_trades if t['type'] == 'sell'])
        
        annual_returns = self._calculate_annual_returns()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_value': final_nav['total_value'],
            'dca_buy_count': dca_buy_count,
            'dca_sell_count': dca_sell_count,
            't_buy_count': 0,
            't_sell_count': 0,
            't_profit': 0,
            'dca_cash': self.dca_cash,
            'dca_value': final_nav['dca_value'],
            't_cash': 0,
            't_value': 0,
            'data_start_date': data_start_date,
            'data_end_date': data_end_date,
            'annual_returns': annual_returns
        }
    
    def _calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            最大回撤
        """
        if not self.daily_nav:
            return 0
        
        peak = self.daily_nav[0]['total_value']
        max_drawdown = 0
        
        for nav in self.daily_nav:
            if nav['total_value'] > peak:
                peak = nav['total_value']
            else:
                drawdown = (peak - nav['total_value']) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率
        
        Returns:
            夏普比率
        """
        if not self.daily_nav or len(self.daily_nav) < 2:
            return 0
        
        returns = []
        for i in range(1, len(self.daily_nav)):
            prev_nav = self.daily_nav[i - 1]
            curr_nav = self.daily_nav[i]
            if prev_nav['total_value'] > 0:
                daily_return = (curr_nav['total_value'] - prev_nav['total_value']) / prev_nav['total_value']
                returns.append(daily_return)
        
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        risk_free_rate = 0.03 / 252
        sharpe_ratio = (avg_return - risk_free_rate) / std_dev * (252 ** 0.5)
        
        return sharpe_ratio
