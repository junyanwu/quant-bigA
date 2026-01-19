#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投+做T策略实现
基于VeighNa框架的定投策略
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime
import json
import os

from strategies.indicators import calculate_all_indicators, get_trading_signals


class DcaTradingStrategy:
    """
    定投+做T策略
    
    策略组成：
    1. 定投部分：定期投资，止盈减仓
    2. 做T部分：根据技术指标进行加仓减仓
    """
    
    def __init__(self, 
                 total_capital: float = 500000.0,
                 dca_ratio: float = 0.7,
                 dca_amount_per_week: float = 1000.0,
                 t_amount_per_trade: float = 5000.0,
                 max_loss_ratio: float = 0.03,
                 profit_target: float = 0.01,
                 commission: float = 0.0003,
                 slippage: float = 0.001):
        """
        初始化策略参数
        
        第十一轮优化后的参数：
        - 定投比例：70%，占主要仓位
        - 做T比例：30%，占次要仓位
        - 定投金额：1000元/周（每周定投）
        - 做T金额：5000元/次（需判断是否有足够仓位做T）
        - 止损：基于ATR（平均真实波幅），当价格跌破买入价 - 2*ATR时止损
        - 平仓信号：MACD柱反转开始下跌（macd_hist < macd_hist_prev）且价格跌破5日均线
        - 手续费：最低5元
        
        策略思路：
        - 定投：不择时，每周定投，高估时分批卖出
        - 做T：基于大盘下跌反弹和MACD反转，需有足够定投仓位
        - 止损：使用ATR动态止损，适应市场波动
        - 平仓：结合MACD柱反转和5日均线，捕捉趋势变化
        
        Args:
            total_capital: 总资金
            dca_ratio: 定投资金比例
            dca_amount_per_week: 每周定投金额
            t_amount_per_trade: 每次做T金额
            max_loss_ratio: 最大亏损比例（止损）
            profit_target: 止盈目标
            commission: 手续费率
            slippage: 滑点率
        """
        self.total_capital = total_capital
        self.dca_capital = total_capital * dca_ratio
        self.t_capital = total_capital * (1 - dca_ratio)
        
        self.dca_amount_per_week = dca_amount_per_week
        self.t_amount_per_trade = t_amount_per_trade
        self.max_loss_ratio = max_loss_ratio
        self.profit_target = profit_target
        self.commission = commission
        self.slippage = slippage
        
        self.dca_positions = {}
        self.t_positions = {}
        self.t_can_add = {}
        
        self.cash = total_capital
        self.dca_cash = self.dca_capital
        self.t_cash = self.t_capital
        
        self.trades = []
        self.dca_trades = []
        self.t_trades = []
        
        self.daily_nav = []
        
        self.params = {
            'total_capital': total_capital,
            'dca_ratio': dca_ratio,
            'dca_amount_per_week': dca_amount_per_week,
            't_amount_per_trade': t_amount_per_trade,
            'max_loss_ratio': max_loss_ratio,
            'profit_target': profit_target,
            'commission': commission,
            'slippage': slippage
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
        
        第十二轮优化后的逻辑：
        - 不择时，每周定投（每周第一个交易日）
        - 仓位超过70%时，且盈利>20%，且macd柱>0且放量且macd柱下跌，则分批卖出
        """
        price = bar_data['close']
        position = self.dca_positions[symbol]
        
        profit_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            profit_ratio = (current_value - position['cost']) / position['cost']
        
        is_first_day_of_week = date.weekday() == 0
        
        if is_first_day_of_week and self.dca_cash >= self.dca_amount_per_week:
            shares = self._calculate_shares(self.dca_amount_per_week, price)
            if shares > 0:
                self._buy_dca(symbol, shares, price, date)
        
        position_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            position_ratio = current_value / (self.dca_cash + current_value)
        
        macd_hist = bar_data.get('macd_hist', 0)
        macd_hist_prev = bar_data.get('macd_hist_prev', 0)
        volume_ratio = bar_data.get('volume_ratio', 1.0)
        
        should_sell = (
            position['shares'] > 0 and
            position_ratio > 0.7 and
            profit_ratio > 0.2 and
            macd_hist > 0 and
            volume_ratio > 1.5 and
            macd_hist < macd_hist_prev
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
        
        第十一轮优化后的逻辑：
        1. 大盘下跌超过2%然后反弹0.3%时分段买入
        2. 大盘下跌超过1%但小于2%，反弹0.2%时买入
        3. MACD柱<0且出现反转，昨天是阳线时买入
        4. 做T买入前需判断是否有足够定投仓位（定投仓位市值 >= 做T金额）
        5. 止损：基于ATR（平均真实波幅），当价格跌破买入价 - 2*ATR时止损
        6. 平仓信号：MACD柱反转开始下跌（macd_hist < macd_hist_prev）且价格跌破5日均线
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
        
        profit_ratio = 0
        if position['shares'] > 0:
            current_value = position['shares'] * price
            profit_ratio = (current_value - position['cost']) / position['cost']
        
        dca_value = dca_position['shares'] * price
        
        if position['shares'] > 0 and atr > 0:
            stop_loss_price = position['avg_price'] - 2 * atr
            if price < stop_loss_price:
                self._sell_t(symbol, position['shares'], price, date)
                return
        
        if position['shares'] > 0 and ma5 > 0 and macd_hist > 0:
            macd_reversing_down = macd_hist < macd_hist_prev
            price_below_ma5 = price < ma5
            if macd_reversing_down and price_below_ma5:
                self._sell_t(symbol, position['shares'], price, date)
                return
        
        if position['shares'] == 0 and self.t_cash >= self.t_amount_per_trade and dca_value >= self.t_amount_per_trade:
            if index_data.get('drop_2_rebound_03', False):
                shares = self._calculate_shares(self.t_amount_per_trade, price)
                if shares > 0:
                    self._buy_t(symbol, shares, price, date)
                    return
            
            if index_data.get('drop_1_rebound_02', False):
                shares = self._calculate_shares(self.t_amount_per_trade, price)
                if shares > 0:
                    self._buy_t(symbol, shares, price, date)
                    return
            
            if macd_hist < 0 and macd_hist_prev > macd_hist_prev2 and is_yang:
                shares = self._calculate_shares(self.t_amount_per_trade, price)
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
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
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
            'data_end_date': final_nav['date'].strftime('%Y-%m-%d')
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
    
    def save_results(self, output_dir: str):
        """
        保存回测结果
        
        Args:
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        params_file = os.path.join(output_dir, 'strategy_params.json')
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(self.params, f, ensure_ascii=False, indent=2)
        
        trades_data = []
        for trade in self.trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            trades_data.append(trade_copy)
        
        trades_file = os.path.join(output_dir, 'trades.csv')
        trades_df = pd.DataFrame(trades_data)
        trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
        
        dca_trades_data = []
        for trade in self.dca_trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            dca_trades_data.append(trade_copy)
        
        dca_trades_file = os.path.join(output_dir, 'dca_trades.csv')
        dca_trades_df = pd.DataFrame(dca_trades_data)
        dca_trades_df.to_csv(dca_trades_file, index=False, encoding='utf-8-sig')
        
        t_trades_data = []
        for trade in self.t_trades:
            trade_copy = trade.copy()
            trade_copy['date'] = trade['date'].strftime('%Y-%m-%d')
            t_trades_data.append(trade_copy)
        
        t_trades_file = os.path.join(output_dir, 't_trades.csv')
        t_trades_df = pd.DataFrame(t_trades_data)
        t_trades_df.to_csv(t_trades_file, index=False, encoding='utf-8-sig')
        
        nav_data = []
        for nav in self.daily_nav:
            nav_copy = nav.copy()
            nav_copy['date'] = nav['date'].strftime('%Y-%m-%d')
            nav_data.append(nav_copy)
        
        nav_file = os.path.join(output_dir, 'daily_nav.csv')
        nav_df = pd.DataFrame(nav_data)
        nav_df.to_csv(nav_file, index=False, encoding='utf-8-sig')
        
        results = self.get_results()
        results_file = os.path.join(output_dir, 'results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
