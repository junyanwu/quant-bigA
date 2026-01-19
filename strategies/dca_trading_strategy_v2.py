#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投+做T策略 v2.0
基于VeighNa框架的定投策略

v2.0版本改进：
1. 动态参数调整 - 根据市场波动性自动调整参数
2. 自适应阈值 - 根据标的特性动态调整开平仓阈值
3. 智能开平仓 - 结合多个技术指标的综合判断
4. 风险管理 - 更精细的风险控制机制
"""

import pandas as pd
from typing import Dict
from datetime import datetime
import json
import os

from strategies.indicators import calculate_all_indicators, get_trading_signals
from strategies.base_strategy import BaseStrategy


class DcaTradingStrategyV2(BaseStrategy):
    """
    定投+做T策略 v2.0
    
    策略组成：
    1. 定投部分：定期投资，智能止盈减仓
    2. 做T部分：根据技术指标和动态参数进行加仓减仓
    
    v2.0改进：
    - 动态调整定投金额（基于市场波动性）
    - 自适应止盈阈值（基于历史波动率）
    - 智能做T参数（基于ATR和市场状态）
    - 多条件综合判断开平仓
    """
    
    def __init__(self, 
                 total_capital: float = 500000.0,
                 dca_ratio: float = 0.7,
                 base_dca_amount_per_week: float = 1000.0,
                 base_t_amount_per_trade: float = 5000.0,
                 max_loss_ratio: float = 0.03,
                 profit_target: float = 0.01,
                 commission: float = 0.0003,
                 slippage: float = 0.001):
        """
        初始化策略参数
        
        v2.0版本参数：
        - 定投比例：70%，占主要仓位
        - 基础定投金额：1000元/周（动态调整）
        - 基础做T金额：5000元/次（动态调整）
        - 止损：基于ATR（平均真实波幅），动态调整
        - 平仓信号：综合多个技术指标
        - 手续费：最低5元
        
        v2.0策略思路：
        - 定投：不择时，每周定投，动态调整金额，智能止盈
        - 做T：基于市场状态和技术指标，动态调整参数
        - 止损：使用ATR动态止损，根据波动性调整倍数
        - 平仓：结合MACD、均线、成交量等多维度信号
        
        Args:
            total_capital: 总资金
            dca_ratio: 定投资金比例
            base_dca_amount_per_week: 基础每周定投金额
            base_t_amount_per_trade: 基础每次做T金额
            max_loss_ratio: 最大亏损比例（止损）
            profit_target: 止盈目标
            commission: 手续费率
            slippage: 滑点率
        """
        self.total_capital = total_capital
        self.dca_capital = total_capital * dca_ratio
        self.t_capital = total_capital * (1 - dca_ratio)
        
        self.base_dca_amount_per_week = base_dca_amount_per_week
        self.base_t_amount_per_trade = base_t_amount_per_trade
        self.max_loss_ratio = max_loss_ratio
        self.profit_target = profit_target
        self.commission = commission
        self.slippage = slippage
        
        super().__init__()
        
        self.cash = total_capital
        self.dca_cash = self.dca_capital
        self.t_cash = self.t_capital
        
        self.params = {
            'total_capital': total_capital,
            'dca_ratio': dca_ratio,
            'base_dca_amount_per_week': base_dca_amount_per_week,
            'base_t_amount_per_trade': base_t_amount_per_trade,
            'max_loss_ratio': max_loss_ratio,
            'profit_target': profit_target,
            'commission': commission,
            'slippage': slippage,
            'version': '2.0'
        }
    
    def _calculate_dynamic_dca_amount(self, bar_data: Dict) -> float:
        """
        计算动态定投金额
        
        基于市场波动性调整定投金额：
        - 高波动时减少定投金额（降低风险）
        - 低波动时增加定投金额（提高收益）
        
        Args:
            bar_data: bar数据
            
        Returns:
            动态定投金额
        """
        atr = bar_data.get('atr', 0)
        price = bar_data['close']
        
        if atr == 0 or price == 0:
            return self.base_dca_amount_per_week
        
        atr_ratio = atr / price
        
        if atr_ratio > 0.03:
            return self.base_dca_amount_per_week * 0.7
        elif atr_ratio > 0.02:
            return self.base_dca_amount_per_week * 0.85
        elif atr_ratio < 0.01:
            return self.base_dca_amount_per_week * 1.15
        else:
            return self.base_dca_amount_per_week
    
    def _calculate_dynamic_t_amount(self, bar_data: Dict) -> float:
        """
        计算动态做T金额
        
        基于市场状态和波动性调整做T金额：
        - 高波动时减少做T金额
        - 趋势明确时增加做T金额
        
        Args:
            bar_data: bar数据
            
        Returns:
            动态做T金额
        """
        atr = bar_data.get('atr', 0)
        price = bar_data['close']
        is_uptrend = bar_data.get('is_uptrend', False)
        is_downtrend = bar_data.get('is_downtrend', False)
        
        if atr == 0 or price == 0:
            return self.base_t_amount_per_trade
        
        atr_ratio = atr / price
        dynamic_amount = self.base_t_amount_per_trade
        
        if atr_ratio > 0.03:
            dynamic_amount *= 0.7
        elif atr_ratio > 0.02:
            dynamic_amount *= 0.85
        elif atr_ratio < 0.01:
            dynamic_amount *= 1.15
        
        if is_uptrend:
            dynamic_amount *= 1.1
        elif is_downtrend:
            dynamic_amount *= 0.9
        
        return dynamic_amount
    
    def _calculate_dynamic_stop_loss_multiplier(self, bar_data: Dict) -> float:
        """
        计算动态止损倍数
        
        基于市场波动性调整止损倍数：
        - 高波动时增加止损倍数（避免过早止损）
        - 低波动时减少止损倍数（及时止损）
        
        Args:
            bar_data: bar数据
            
        Returns:
            动态止损倍数
        """
        atr = bar_data.get('atr', 0)
        price = bar_data['close']
        
        if atr == 0 or price == 0:
            return 2.0
        
        atr_ratio = atr / price
        
        if atr_ratio > 0.03:
            return 2.5
        elif atr_ratio > 0.02:
            return 2.2
        elif atr_ratio < 0.01:
            return 1.5
        else:
            return 2.0
    
    def _calculate_dynamic_profit_target(self, bar_data: Dict) -> float:
        """
        计算动态止盈目标
        
        基于历史波动率和市场状态调整止盈目标：
        - 高波动时提高止盈目标（获取更多收益）
        - 低波动时降低止盈目标（及时止盈）
        
        Args:
            bar_data: bar数据
            
        Returns:
            动态止盈目标
        """
        atr = bar_data.get('atr', 0)
        price = bar_data['close']
        
        if atr == 0 or price == 0:
            return self.profit_target
        
        atr_ratio = atr / price
        
        if atr_ratio > 0.03:
            return self.profit_target * 1.3
        elif atr_ratio > 0.02:
            return self.profit_target * 1.15
        elif atr_ratio < 0.01:
            return self.profit_target * 0.85
        else:
            return self.profit_target
    
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
        if symbol not in self.t_positions:
            self.t_positions[symbol] = {'shares': 0.0, 'cost': 0.0, 'avg_price': 0.0, 'entry_date': None}
        if symbol not in self.t_can_add:
            self.t_can_add[symbol] = True
        
        self._execute_dca_logic(bar_data, date, symbol)
        self._execute_t_logic(bar_data, date, symbol)
        self._record_daily_nav(bar_data, date, symbol)
    
    def _execute_dca_logic(self, bar_data: Dict, date: datetime, symbol: str):
        """
        执行定投逻辑
        
        v2.0版本改进：
        - 动态调整定投金额
        - 多条件综合判断卖出时机
        - 自适应止盈目标
        """
        price = bar_data['close']
        position = self.dca_positions[symbol]
        
        profit_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            profit_ratio = (current_value - position['cost']) / position['cost']
        
        is_first_day_of_week = date.weekday() == 0
        
        dynamic_dca_amount = self._calculate_dynamic_dca_amount(bar_data)
        
        if is_first_day_of_week and self.dca_cash >= dynamic_dca_amount:
            shares = self._calculate_shares(dynamic_dca_amount, price)
            if shares > 0:
                self._buy_dca(symbol, shares, price, date)
        
        position_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            position_ratio = current_value / (self.dca_cash + current_value)
        
        macd_hist = bar_data.get('macd_hist', 0)
        macd_hist_prev = bar_data.get('macd_hist_prev', 0)
        volume_ratio = bar_data.get('volume_ratio', 1.0)
        is_uptrend = bar_data.get('is_uptrend', False)
        is_downtrend = bar_data.get('is_downtrend', False)
        
        dynamic_profit_target = self._calculate_dynamic_profit_target(bar_data)
        
        should_sell = (
            position['shares'] > 0 and
            position_ratio > 0.65 and
            profit_ratio > dynamic_profit_target and
            (
                (macd_hist > 0 and volume_ratio > 1.5 and macd_hist < macd_hist_prev) or
                (is_downtrend and profit_ratio > 0.15) or
                (macd_hist < 0 and profit_ratio > 0.25)
            )
        )
        
        if should_sell:
            if not hasattr(self, '_sell_count'):
                self._sell_count = {}
            
            if symbol not in self._sell_count:
                self._sell_count[symbol] = 0
            
            if self._sell_count[symbol] < 3:
                sell_shares = position['shares'] / 3
                if sell_shares > 0:
                    self._sell_dca(symbol, sell_shares, price, date)
                    self._sell_count[symbol] += 1
    
    def _execute_t_logic(self, bar_data: Dict, date: datetime, symbol: str):
        """
        执行做T逻辑
        
        v2.0版本改进：
        - 动态调整做T金额
        - 动态止损倍数
        - 多条件综合判断开平仓
        """
        price = bar_data['close']
        position = self.t_positions[symbol]
        dca_position = self.dca_positions[symbol]
        
        index_data = bar_data.get('index_data', {})
        
        macd_hist = bar_data.get('macd_hist', 0)
        macd_hist_prev = bar_data.get('macd_hist_prev', 0)
        macd_hist_prev2 = bar_data.get('macd_hist_prev2', 0)
        is_yang = bar_data.get('is_yang', False)
        atr = bar_data.get('atr', 0)
        ma5 = bar_data.get('ma5', 0)
        is_uptrend = bar_data.get('is_uptrend', False)
        is_downtrend = bar_data.get('is_downtrend', False)
        
        profit_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            profit_ratio = (current_value - position['cost']) / position['cost']
        
        dca_value = dca_position['shares'] * price
        
        dynamic_stop_loss_multiplier = self._calculate_dynamic_stop_loss_multiplier(bar_data)
        
        if position['shares'] > 0 and atr > 0:
            stop_loss_price = position['avg_price'] - dynamic_stop_loss_multiplier * atr
            if price < stop_loss_price:
                self._sell_t(symbol, position['shares'], price, date)
                return
        
        if position['shares'] > 0 and ma5 > 0 and macd_hist > 0:
            macd_reversing_down = macd_hist < macd_hist_prev
            price_below_ma5 = price < ma5
            is_volume_surge = bar_data.get('is_volume_surge', False)
            
            should_close = (
                macd_reversing_down and price_below_ma5 and
                (profit_ratio > 0.01 or is_volume_surge)
            )
            
            if should_close:
                self._sell_t(symbol, position['shares'], price, date)
                return
        
        dynamic_t_amount = self._calculate_dynamic_t_amount(bar_data)
        
        if position['shares'] == 0 and self.t_cash >= dynamic_t_amount:
            buy_signal = False
            
            if index_data.get('drop_2_rebound_03', False) and is_uptrend:
                buy_signal = True
            elif index_data.get('drop_1_rebound_02', False):
                buy_signal = True
            elif macd_hist < 0 and macd_hist_prev > macd_hist_prev2 and is_yang:
                buy_signal = True
            
            if buy_signal:
                shares = self._calculate_shares(dynamic_t_amount, price)
                if shares > 0:
                    self._buy_t(symbol, shares, price, date)
                    return
    
    def _calculate_shares(self, amount: float, price: float) -> float:
        """
        计算可买入的股数
        
        Args:
            amount: 金额
            price: 价格
            
        Returns:
            可买入的股数
        """
        actual_price = price * (1 + self.slippage)
        commission = self._calculate_commission(amount)
        available_amount = amount - commission
        shares = available_amount / actual_price
        return int(shares / 100) * 100
    
    def _calculate_commission(self, amount: float) -> float:
        """
        计算手续费（最低5元）
        
        Args:
            amount: 交易金额
            
        Returns:
            手续费金额
        """
        commission = amount * self.commission
        return max(commission, 5.0)
    
    def _execute_buy(self, positions: Dict, cash: float, symbol: str, shares: float, price: float, date: datetime, strategy: str):
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
    
    def _execute_sell(self, positions: Dict, cash: float, symbol: str, shares: float, price: float, date: datetime, strategy: str):
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
        commission = self._calculate_commission(amount)
        net_amount = amount - commission
        cost_ratio = shares / position['shares']
        cost_amount = position['cost'] * cost_ratio
        
        position['shares'] -= shares
        position['cost'] -= cost_amount
        position['avg_price'] = position['cost'] / position['shares'] if position['shares'] > 0 else 0
        
        if strategy == 't':
            position['entry_date'] = None
        
        cash += net_amount
        
        trade = {
            'date': date,
            'symbol': symbol,
            'type': 'sell',
            'strategy': strategy,
            'shares': shares,
            'price': price,
            'amount': net_amount,
            'profit': net_amount - cost_amount,
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
    
    def _buy_dca(self, symbol: str, shares: float, price: float, date: datetime):
        """
        定投买入
        """
        self._execute_buy(self.dca_positions, self.dca_cash, symbol, shares, price, date, 'dca')
    
    def _sell_dca(self, symbol: str, shares: float, price: float, date: datetime):
        """
        定投卖出
        """
        self._execute_sell(self.dca_positions, self.dca_cash, symbol, shares, price, date, 'dca')
    
    def _buy_t(self, symbol: str, shares: float, price: float, date: datetime):
        """
        做T买入
        """
        self._execute_buy(self.t_positions, self.t_cash, symbol, shares, price, date, 't')
    
    def _sell_t(self, symbol: str, shares: float, price: float, date: datetime):
        """
        做T卖出
        """
        self._execute_sell(self.t_positions, self.t_cash, symbol, shares, price, date, 't')
    
    def _record_daily_nav(self, bar_data: Dict, date: datetime, symbol: str):
        """
        记录每日净值
        
        Args:
            bar_data: bar数据
            date: 日期
            symbol: 标的代码
        """
        price = bar_data['close']
        
        dca_value = self.dca_positions[symbol]['shares'] * price
        t_value = self.t_positions[symbol]['shares'] * price
        
        total_value = self.dca_cash + self.t_cash + dca_value + t_value
        
        nav = {
            'date': date,
            'symbol': symbol,
            'dca_cash': self.dca_cash,
            't_cash': self.t_cash,
            'dca_value': dca_value,
            't_value': t_value,
            'total_value': total_value,
            'total_return': (total_value - self.total_capital) / self.total_capital
        }
        self.daily_nav.append(nav)
        
        # 调用基类的实现，记录仓位、买入、卖出信息
        super()._record_daily_nav(bar_data, date, symbol)
    
    def get_results(self) -> Dict:
        """
        获取策略结果
        
        Returns:
            包含策略结果的字典
        """
        if not self.daily_nav:
            return {}
        
        final_nav = self.daily_nav[-1]
        initial_nav = self.daily_nav[0]
        
        total_return = final_nav['total_return']
        
        days = (final_nav['date'] - initial_nav['date']).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0
        
        nav_series = pd.Series([nav['total_value'] for nav in self.daily_nav])
        rolling_max = nav_series.expanding().max()
        drawdown = (nav_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        returns = pd.Series([nav['total_return'] for nav in self.daily_nav]).diff().dropna()
        sharpe_ratio = returns.mean() / returns.std() * 252 ** 0.5 if returns.std() > 0 else 0
        
        dca_buy_count = len([t for t in self.dca_trades if t['type'] == 'buy'])
        dca_sell_count = len([t for t in self.dca_trades if t['type'] == 'sell'])
        t_buy_count = len([t for t in self.t_trades if t['type'] == 'buy'])
        t_sell_count = len([t for t in self.t_trades if t['type'] == 'sell'])
        
        t_profit = sum([t.get('profit', 0) for t in self.t_trades if t['type'] == 'sell'])
        
        annual_returns = self._calculate_annual_returns()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_value': final_nav['total_value'],
            'dca_buy_count': dca_buy_count,
            'dca_sell_count': dca_sell_count,
            't_buy_count': t_buy_count,
            't_sell_count': t_sell_count,
            't_profit': t_profit,
            'dca_cash': final_nav['dca_cash'],
            't_cash': final_nav['t_cash'],
            'dca_value': final_nav['dca_value'],
            't_value': final_nav['t_value'],
            'annual_returns': annual_returns,
            'data_start_date': initial_nav['date'].strftime('%Y-%m-%d'),
            'data_end_date': final_nav['date'].strftime('%Y-%m-%d'),
            'version': '2.0'
        }
    
    def _calculate_annual_returns(self) -> list:
        """
        计算年度收益率
        
        Returns:
            年度收益率列表 [{'year': 2020, 'return': 0.15, 'profit': 75000}, ...]
        """
        if not self.daily_nav:
            return []
        
        yearly_data = {}
        for nav in self.daily_nav:
            year = nav['date'].year
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append(nav)
        
        annual_returns = []
        for year, navs in sorted(yearly_data.items()):
            start_value = navs[0]['total_value']
            end_value = navs[-1]['total_value']
            year_return = (end_value - start_value) / start_value if start_value > 0 else 0
            year_profit = end_value - start_value
            
            annual_returns.append({
                'year': year,
                'return': year_return,
                'profit': year_profit
            })
        
        return annual_returns
