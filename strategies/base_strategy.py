#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略基类
定义所有策略的统一接口，确保v1、v2、v3策略保持一致性
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import json
import os


class BaseStrategy(ABC):
    """
    策略基类
    
    所有策略必须继承此类并实现抽象方法，确保数据输出格式一致
    """
    
    def __init__(self):
        """
        初始化策略基类
        """
        self.params = {}
        
        self.dca_positions = {}
        self.t_positions = {}
        self.t_can_add = {}
        
        self.cash = 0.0
        self.dca_cash = 0.0
        self.t_cash = 0.0
        
        self.trades = []
        self.dca_trades = []
        self.t_trades = []
        
        self.daily_nav = []
        
        # 记录每日的仓位、买入、卖出信息
        self.daily_position_info = []
        
        # 记录每日的买入、卖出金额
        self.daily_buy_amount = 0.0
        self.daily_sell_amount = 0.0
    
    @abstractmethod
    def on_bar(self, bar_data: Dict, date: datetime):
        """
        每个bar的回调函数（抽象方法，子类必须实现）
        
        Args:
            bar_data: 包含OHLCV和技术指标的数据
            date: 当前日期
        """
        pass
    
    @abstractmethod
    def get_results(self) -> Dict:
        """
        获取策略结果（抽象方法，子类必须实现）
        
        Returns:
            包含策略结果的字典，格式必须包含以下字段：
            - total_return: 总收益率
            - annual_return: 年化收益率
            - max_drawdown: 最大回撤
            - sharpe_ratio: 夏普比率
            - final_value: 最终价值
            - dca_buy_count: 定投买入次数
            - dca_sell_count: 定投卖出次数
            - t_buy_count: 做T买入次数
            - t_sell_count: 做T卖出次数
            - t_profit: 做T利润
            - data_start_date: 数据开始日期
            - data_end_date: 数据结束日期
            - annual_returns: 年度收益列表
        """
        pass
    
    def save_results(self, output_dir: str):
        """
        保存策略结果到文件
        
        Args:
            output_dir: 输出目录
        """
        import os
        import json
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存策略参数
        params_file = os.path.join(output_dir, 'strategy_params.json')
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(self.params, f, ensure_ascii=False, indent=2)
        
        # 保存所有交易记录
        trades_data = []
        for trade in self.trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            trades_data.append(trade_copy)
        
        trades_file = os.path.join(output_dir, 'trades.csv')
        trades_df = pd.DataFrame(trades_data)
        trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
        
        # 保存定投交易记录
        dca_trades_data = []
        for trade in self.dca_trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            dca_trades_data.append(trade_copy)
        
        dca_trades_file = os.path.join(output_dir, 'dca_trades.csv')
        dca_trades_df = pd.DataFrame(dca_trades_data)
        dca_trades_df.to_csv(dca_trades_file, index=False, encoding='utf-8-sig')
        
        # 保存做T交易记录
        t_trades_data = []
        for trade in self.t_trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            t_trades_data.append(trade_copy)
        
        t_trades_file = os.path.join(output_dir, 't_trades.csv')
        t_trades_df = pd.DataFrame(t_trades_data)
        t_trades_df.to_csv(t_trades_file, index=False, encoding='utf-8-sig')
        
        # 保存每日净值
        nav_data = []
        for nav in self.daily_nav:
            nav_copy = nav.copy()
            nav_copy['date'] = nav['date'].strftime('%Y-%m-%d')
            nav_data.append(nav_copy)
        
        nav_file = os.path.join(output_dir, 'daily_nav.csv')
        nav_df = pd.DataFrame(nav_data)
        nav_df.to_csv(nav_file, index=False, encoding='utf-8-sig')
        
        # 保存每日仓位信息
        position_info_data = []
        for info in self.daily_position_info:
            info_copy = info.copy()
            info_copy['date'] = info['date'].strftime('%Y-%m-%d')
            position_info_data.append(info_copy)
        
        position_info_file = os.path.join(output_dir, 'daily_position_info.csv')
        position_info_df = pd.DataFrame(position_info_data)
        position_info_df.to_csv(position_info_file, index=False, encoding='utf-8-sig')
        
        # 保存结果JSON
        results = self.get_results()
        results_file = os.path.join(output_dir, 'results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def _calculate_commission(self, amount: float) -> float:
        """
        计算手续费
        
        Args:
            amount: 交易金额
            
        Returns:
            手续费
        """
        commission = amount * self.params.get('commission', 0.0003)
        return max(commission, 5.0)
    
    def _execute_buy(self, positions: Dict, cash: float, symbol: str, 
                    shares: float, price: float, date: datetime, strategy: str):
        """
        通用买入操作
        
        Args:
            positions: 持仓字典
            cash: 可用资金
            symbol: 标的代码
            shares: 买入股数
            price: 价格
            date: 日期
            strategy: 策略类型（'dca'或't'）
        """
        position = positions[symbol]
        amount = shares * price
        cost = amount + self._calculate_commission(amount)
        
        total_shares = position['shares'] + shares
        total_cost = position['cost'] + cost
        avg_price = total_cost / total_shares if total_shares > 0 else 0
        
        position['shares'] = total_shares
        position['cost'] = total_cost
        position['avg_price'] = avg_price
        
        if strategy == 't':
            position['entry_date'] = date
        
        cash -= cost
        
        trade = {
            'date': date,
            'symbol': symbol,
            'type': 'buy',
            'strategy': strategy,
            'shares': shares,
            'price': price,
            'amount': cost,
            'cash_after': cash
        }
        
        if strategy == 'dca':
            self.dca_cash = cash
            self.dca_trades.append(trade)
        else:
            self.t_cash = cash
            self.t_trades.append(trade)
        
        self.trades.append(trade)
        
        # 更新每日买入金额
        self.daily_buy_amount += cost
    
    def _execute_sell(self, positions: Dict, cash: float, symbol: str, 
                     shares: float, price: float, date: datetime, strategy: str):
        """
        通用卖出操作
        
        Args:
            positions: 持仓字典
            cash: 可用资金
            symbol: 标的代码
            shares: 卖出股数
            price: 价格
            date: 日期
            strategy: 策略类型（'dca'或't'）
        """
        position = positions[symbol]
        amount = shares * price
        cost_amount = position['avg_price'] * shares
        commission = self._calculate_commission(amount)
        net_amount = amount - commission
        profit = net_amount - cost_amount
        
        position['shares'] -= shares
        position['cost'] -= cost_amount
        if position['shares'] == 0:
            position['avg_price'] = 0
        
        cash += net_amount
        
        trade = {
            'date': date,
            'symbol': symbol,
            'type': 'sell',
            'strategy': strategy,
            'shares': shares,
            'price': price,
            'amount': net_amount,
            'profit': profit,
            'cash_after': cash
        }
        
        if strategy == 'dca':
            self.dca_cash = cash
            self.dca_trades.append(trade)
        else:
            self.t_cash = cash
            self.t_trades.append(trade)
        
        self.trades.append(trade)
        
        # 更新每日卖出金额
        self.daily_sell_amount += net_amount
    
    def _execute_sell(self, positions: Dict, cash: float, symbol: str, 
                     shares: float, price: float, date: datetime, strategy: str):
        """
        通用卖出操作
        
        Args:
            positions: 持仓字典
            cash: 可用资金
            symbol: 标的代码
            shares: 卖出股数
            price: 价格
            date: 日期
            strategy: 策略类型（'dca'或't'）
        """
        position = positions[symbol]
        amount = shares * price
        cost_amount = position['avg_price'] * shares
        commission = self._calculate_commission(amount)
        net_amount = amount - commission
        profit = net_amount - cost_amount
        
        position['shares'] -= shares
        position['cost'] -= cost_amount
        if position['shares'] == 0:
            position['avg_price'] = 0
        
        cash += net_amount
        
        trade = {
            'date': date,
            'symbol': symbol,
            'type': 'sell',
            'strategy': strategy,
            'shares': shares,
            'price': price,
            'amount': net_amount,
            'profit': profit,
            'cash_after': cash
        }
        
        if strategy == 'dca':
            self.dca_cash = cash
            self.dca_trades.append(trade)
        else:
            self.t_cash = cash
            self.t_trades.append(trade)
        
        self.trades.append(trade)
    
    def _calculate_annual_returns(self) -> list:
        """
        计算年度收益
        
        Returns:
            年度收益列表，每个元素包含：
            - year: 年份
            - return: 年度收益率
            - profit: 年度利润
        """
        if not self.daily_nav:
            return []
        
        annual_returns = {}
        for nav in self.daily_nav:
            year = nav['date'].year
            if year not in annual_returns:
                annual_returns[year] = {'year': year, 'return': 0, 'profit': 0}
            annual_returns[year]['profit'] += nav.get('profit', 0)
        
        initial_nav = self.daily_nav[0]
        for year in sorted(annual_returns.keys()):
            year_navs = [nav for nav in self.daily_nav if nav['date'].year == year]
            if year_navs:
                year_start = year_navs[0]
                year_end = year_navs[-1]
                if year_start['total_value'] > 0:
                    annual_returns[year]['return'] = (year_end['total_value'] - year_start['total_value']) / year_start['total_value']
        
        return list(annual_returns.values())
    
    def _record_daily_nav(self, bar_data: Dict, date: datetime, symbol: str):
        """
        记录每日净值
        
        Args:
            bar_data: 包含OHLCV和技术指标的数据
            date: 当前日期
            symbol: 标的代码
        """
        price = bar_data['close']
        
        dca_value = self.dca_positions.get(symbol, {}).get('shares', 0) * price
        t_value = self.t_positions.get(symbol, {}).get('shares', 0) * price
        
        total_value = self.dca_cash + self.t_cash + dca_value + t_value
        initial_value = self.params.get('total_capital', 0)
        total_return = (total_value - initial_value) / initial_value if initial_value > 0 else 0
        
        nav = {
            'date': date,
            'symbol': symbol,
            'price': price,
            'dca_cash': self.dca_cash,
            't_cash': self.t_cash,
            'dca_value': dca_value,
            't_value': t_value,
            'total_value': total_value,
            'total_return': total_return
        }
        
        self.daily_nav.append(nav)
        
        # 记录每日的仓位、买入、卖出信息
        position_info = {
            'date': date,
            'symbol': symbol,
            'position': (dca_value + t_value) / 10000,  # 转换为万元
            'buy_amount': self.daily_buy_amount / 10000,  # 转换为万元
            'sell_amount': self.daily_sell_amount / 10000  # 转换为万元
        }
        
        self.daily_position_info.append(position_info)
        
        # 重置每日买入、卖出金额
        self.daily_buy_amount = 0.0
        self.daily_sell_amount = 0.0
