#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版MACD策略测试 - 不依赖VeighNa框架
直接使用akshare获取数据，实现MACD策略回测
"""

import pandas as pd
import numpy as np
import akshare as ak
import talib
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import json


class SimpleMACDStrategy:
    """简化版MACD策略回测"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, 
                 stop_loss=0.05, take_profit=0.10):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
    def get_stock_data(self, symbol='000001', start_date='2020-01-01', end_date='2024-12-31'):
        """获取股票数据"""
        try:
            # 获取上证指数数据作为测试
            df = ak.stock_zh_index_hist(symbol=symbol, period="daily", 
                                       start_date=start_date, end_date=end_date)
            
            if df.empty:
                print(f"获取 {symbol} 数据失败")
                return pd.DataFrame()
            
            # 标准化列名
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                         'change_percent', 'change_amount', 'turnover']
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            print(f"成功获取 {symbol} 数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_macd(self, close_prices):
        """计算MACD指标"""
        try:
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices, 
                fastperiod=self.fast_period, 
                slowperiod=self.slow_period, 
                signalperiod=self.signal_period
            )
            return macd, macd_signal, macd_hist
        except Exception as e:
            print(f"计算MACD失败: {e}")
            return None, None, None
    
    def backtest_strategy(self, data):
        """运行策略回测"""
        if data.empty:
            return {}
        
        # 计算MACD指标
        macd, macd_signal, macd_hist = self.calculate_macd(data['close'].values)
        
        if macd is None:
            return {}
        
        # 初始化回测变量
        cash = 1000000  # 初始资金
        position = 0     # 持仓数量
        trades = []      # 交易记录
        portfolio_value = []  # 组合价值
        
        # 生成交易信号
        for i in range(1, len(data)):
            if i < self.slow_period + 1:
                continue
                
            current_price = data['close'].iloc[i]
            current_date = data.index[i]
            
            # 计算当前持仓价值
            current_value = cash + position * current_price
            portfolio_value.append(current_value)
            
            # MACD金叉死叉判断
            prev_macd = macd[i-1] if not np.isnan(macd[i-1]) else 0
            prev_signal = macd_signal[i-1] if not np.isnan(macd_signal[i-1]) else 0
            curr_macd = macd[i] if not np.isnan(macd[i]) else 0
            curr_signal = macd_signal[i] if not np.isnan(macd_signal[i]) else 0
            
            # 金叉：MACD上穿信号线
            golden_cross = (curr_macd > curr_signal and prev_macd <= prev_signal)
            
            # 死叉：MACD下穿信号线
            death_cross = (curr_macd < curr_signal and prev_macd >= prev_signal)
            
            # 执行交易逻辑
            if golden_cross and position == 0:
                # 买入
                shares_to_buy = int(cash * 0.95 / current_price)  # 95%仓位
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price
                    cash -= cost
                    position += shares_to_buy
                    
                    trades.append({
                        'date': current_date,
                        'action': 'BUY',
                        'price': current_price,
                        'shares': shares_to_buy,
                        'value': cost
                    })
            
            elif death_cross and position > 0:
                # 卖出
                sell_value = position * current_price
                cash += sell_value
                
                trades.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'shares': position,
                    'value': sell_value
                })
                
                position = 0
        
        # 计算最终价值
        final_value = cash + position * data['close'].iloc[-1]
        
        return {
            'trades': trades,
            'portfolio_value': portfolio_value,
            'final_value': final_value,
            'initial_capital': 1000000,
            'total_return': (final_value - 1000000) / 1000000 * 100
        }
    
    def calculate_performance(self, result):
        """计算绩效指标"""
        if not result or 'trades' not in result:
            return {}
        
        trades = result['trades']
        portfolio_value = result['portfolio_value']
        
        if not trades:
            return {}
        
        # 基本统计
        total_trades = len(trades) // 2  # 买卖成对
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0
        
        # 计算每笔交易的盈亏
        trade_pnls = []
        for i in range(0, len(trades)-1, 2):
            if trades[i]['action'] == 'BUY' and trades[i+1]['action'] == 'SELL':
                buy_price = trades[i]['price']
                sell_price = trades[i+1]['price']
                shares = trades[i]['shares']
                
                pnl = (sell_price - buy_price) * shares
                total_pnl += pnl
                trade_pnls.append(pnl)
                
                if pnl > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
        
        # 计算绩效指标
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        avg_pnl = np.mean(trade_pnls) if trade_pnls else 0
        
        # 最大回撤
        if portfolio_value:
            cumulative_returns = [v/1000000 - 1 for v in portfolio_value]
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = cumulative_returns - running_max
            max_drawdown = np.min(drawdown) * 100
        else:
            max_drawdown = 0
        
        # 夏普比率（简化计算）
        if trade_pnls:
            sharpe_ratio = np.mean(trade_pnls) / np.std(trade_pnls) if np.std(trade_pnls) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(avg_pnl, 2),
            'total_return': round(result['total_return'], 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2)
        }
    
    def plot_results(self, data, result):
        """绘制回测结果图表"""
        if not result or 'portfolio_value' not in result:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 价格和MACD指标
        axes[0, 0].plot(data.index, data['close'], label='收盘价')
        axes[0, 0].set_title('价格走势')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 2. 累计收益曲线
        portfolio_value = result['portfolio_value']
        if portfolio_value:
            dates = data.index[-len(portfolio_value):]
            axes[0, 1].plot(dates, portfolio_value)
            axes[0, 1].set_title('组合价值变化')
            axes[0, 1].set_ylabel('组合价值')
            axes[0, 1].grid(True)
        
        # 3. 交易盈亏分布
        trades = result['trades']
        if trades:
            trade_pnls = []
            for i in range(0, len(trades)-1, 2):
                if trades[i]['action'] == 'BUY' and trades[i+1]['action'] == 'SELL':
                    pnl = (trades[i+1]['price'] - trades[i]['price']) * trades[i]['shares']
                    trade_pnls.append(pnl)
            
            if trade_pnls:
                axes[1, 0].hist(trade_pnls, bins=20, alpha=0.7)
                axes[1, 0].set_title('交易盈亏分布')
                axes[1, 0].set_xlabel('盈亏金额')
                axes[1, 0].set_ylabel('频次')
                axes[1, 0].grid(True)
        
        # 4. 绩效指标
        performance = self.calculate_performance(result)
        if performance:
            metrics = ['胜率', '总收益', '夏普比率']
            values = [performance['win_rate'], performance['total_return'], performance['sharpe_ratio']]
            axes[1, 1].bar(metrics, values)
            axes[1, 1].set_title('关键绩效指标')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig('macd_backtest_results.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, performance):
        """生成回测报告"""
        report = f"""
=== MACD策略回测报告 ===

策略参数:
- 快线周期: {self.fast_period}
- 慢线周期: {self.slow_period}  
- 信号周期: {self.signal_period}
- 止损比例: {self.stop_loss * 100}%
- 止盈比例: {self.take_profit * 100}%

绩效指标:
- 总交易次数: {performance.get('total_trades', 0)}
- 盈利交易: {performance.get('winning_trades', 0)}
- 亏损交易: {performance.get('losing_trades', 0)}
- 胜率: {performance.get('win_rate', 0)}%
- 总盈亏: {performance.get('total_pnl', 0):,.2f}
- 平均盈亏: {performance.get('avg_pnl', 0):,.2f}
- 总收益率: {performance.get('total_return', 0)}%
- 夏普比率: {performance.get('sharpe_ratio', 0)}
- 最大回撤: {performance.get('max_drawdown', 0)}%

策略分析:
1. 胜率 {performance.get('win_rate', 0)}% 表明策略的择时能力
2. 总收益率 {performance.get('total_return', 0)}% 显示策略的盈利能力
3. 夏普比率 {performance.get('sharpe_ratio', 0)} 反映风险调整后收益
4. 最大回撤 {performance.get('max_drawdown', 0)}% 衡量策略的风险控制能力
"""
        return report


def main():
    """主测试函数"""
    print("=== MACD策略回测测试 ===")
    
    # 创建策略实例
    strategy = SimpleMACDStrategy(
        fast_period=12,
        slow_period=26,
        signal_period=9,
        stop_loss=0.05,
        take_profit=0.10
    )
    
    # 获取测试数据（上证指数）
    print("正在获取测试数据...")
    data = strategy.get_stock_data(symbol='000001', start_date='2020-01-01', end_date='2024-12-31')
    
    if data.empty:
        print("数据获取失败，无法进行回测")
        return
    
    # 运行回测
    print("正在运行MACD策略回测...")
    result = strategy.backtest_strategy(data)
    
    if not result:
        print("回测失败")
        return
    
    # 计算绩效指标
    performance = strategy.calculate_performance(result)
    
    # 生成报告
    report = strategy.generate_report(performance)
    print(report)
    
    # 绘制图表
    print("正在生成图表...")
    strategy.plot_results(data, result)
    
    # 保存结果
    with open('backtest_summary.json', 'w', encoding='utf-8') as f:
        json.dump({
            'strategy_params': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            'performance': performance,
            'trades_count': len(result.get('trades', [])) // 2
        }, f, indent=2, ensure_ascii=False)
    
    print("回测完成！结果已保存到 backtest_summary.json 和 macd_backtest_results.png")


if __name__ == "__main__":
    main()