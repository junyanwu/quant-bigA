#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化MACD策略测试 - 使用模拟数据
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class SimpleMACDStrategy:
    """简化版MACD策略"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def generate_test_data(self, days=1000, start_price=100):
        """生成模拟股价数据"""
        dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
        
        # 生成随机游走价格序列
        returns = np.random.normal(0.0005, 0.02, days)  # 日均收益0.05%，波动率2%
        prices = [start_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.01 for p in prices],  # 最高价 = 收盘价 * 1.01
            'low': [p * 0.99 for p in prices],   # 最低价 = 收盘价 * 0.99
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        return df
    
    def calculate_ema(self, prices, period):
        """计算指数移动平均"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_macd(self, close_prices):
        """计算MACD指标"""
        # 计算快线EMA和慢线EMA
        ema_fast = self.calculate_ema(close_prices, self.fast_period)
        ema_slow = self.calculate_ema(close_prices, self.slow_period)
        
        # MACD线 = 快线 - 慢线
        macd_line = ema_fast - ema_slow
        
        # 信号线 = MACD线的EMA
        signal_line = self.calculate_ema(macd_line, self.signal_period)
        
        # 柱状图 = MACD线 - 信号线
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def backtest_strategy(self, data):
        """运行策略回测"""
        if data.empty:
            return {}
        
        # 计算MACD指标
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])
        
        # 初始化回测变量
        cash = 1000000  # 初始资金
        position = 0     # 持仓数量
        trades = []      # 交易记录
        portfolio_values = []  # 组合价值历史
        
        # 生成交易信号
        for i in range(self.slow_period + 1, len(data)):
            current_price = data['close'].iloc[i]
            current_date = data.index[i]
            
            # 计算当前组合价值
            current_value = cash + position * current_price
            portfolio_values.append(current_value)
            
            # MACD金叉死叉判断
            prev_macd = macd_line.iloc[i-1]
            prev_signal = signal_line.iloc[i-1]
            curr_macd = macd_line.iloc[i]
            curr_signal = signal_line.iloc[i]
            
            # 金叉：MACD上穿信号线
            golden_cross = (curr_macd > curr_signal and prev_macd <= prev_signal)
            
            # 死叉：MACD下穿信号线
            death_cross = (curr_macd < curr_signal and prev_macd >= prev_signal)
            
            # 执行交易逻辑
            if golden_cross and position == 0:
                # 买入信号
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
                # 卖出信号
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
        
        # 计算最终价值（平仓剩余持仓）
        if position > 0:
            sell_value = position * data['close'].iloc[-1]
            cash += sell_value
            position = 0
        
        final_value = cash
        
        return {
            'trades': trades,
            'portfolio_values': portfolio_values,
            'final_value': final_value,
            'initial_capital': 1000000,
            'total_return': (final_value - 1000000) / 1000000 * 100
        }
    
    def calculate_performance(self, result):
        """计算绩效指标"""
        if not result or 'trades' not in result:
            return {}
        
        trades = result['trades']
        
        if len(trades) < 2:
            return {}
        
        # 基本统计
        total_trades = len(trades) // 2  # 买卖成对
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0
        trade_pnls = []
        
        # 计算每笔交易的盈亏
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
        
        # 最大回撤（简化计算）
        portfolio_values = result.get('portfolio_values', [])
        if portfolio_values:
            returns = [(v/1000000 - 1) * 100 for v in portfolio_values]
            running_max = np.maximum.accumulate(returns)
            drawdown = returns - running_max
            max_drawdown = np.min(drawdown)
        else:
            max_drawdown = 0
        
        # 夏普比率（简化计算）
        if trade_pnls and len(trade_pnls) > 1:
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
    
    def generate_report(self, performance):
        """生成回测报告"""
        report = f"""
=== MACD策略回测报告 ===

策略参数:
- 快线周期(EMA{self.fast_period}): {self.fast_period}
- 慢线周期(EMA{self.slow_period}): {self.slow_period}  
- 信号周期(EMA{self.signal_period}): {self.signal_period}

绩效指标:
- 总交易次数: {performance.get('total_trades', 0)}
- 盈利交易: {performance.get('winning_trades', 0)}
- 亏损交易: {performance.get('losing_trades', 0)}
- 胜率: {performance.get('win_rate', 0)}%
- 总盈亏: {performance.get('total_pnl', 0):,.2f} 元
- 平均盈亏: {performance.get('avg_pnl', 0):,.2f} 元
- 总收益率: {performance.get('total_return', 0)}%
- 夏普比率: {performance.get('sharpe_ratio', 2)}
- 最大回撤: {performance.get('max_drawdown', 0)}%

策略分析:
1. 交易频率: {performance.get('total_trades', 0)} 次交易，平均持仓周期适中
2. 盈利能力: 胜率 {performance.get('win_rate', 0)}%，总收益 {performance.get('total_return', 0)}%
3. 风险控制: 最大回撤 {performance.get('max_drawdown', 0)}%，反映策略风险承受能力
4. 风险调整收益: 夏普比率 {performance.get('sharpe_ratio', 2)}，衡量单位风险下的收益

策略建议:
- 如果胜率 > 50% 且夏普比率 > 1，策略表现良好
- 如果最大回撤 > 20%，需要考虑加强风险控制
- 根据回测结果调整MACD参数优化策略表现
"""
        return report


def main():
    """主测试函数"""
    print("=== MACD策略回测测试 ===")
    print("使用模拟数据进行策略验证...")
    
    # 创建策略实例
    strategy = SimpleMACDStrategy(
        fast_period=12,
        slow_period=26,
        signal_period=9
    )
    
    # 生成模拟数据
    print("生成模拟股价数据...")
    data = strategy.generate_test_data(days=1000, start_price=100)
    print(f"生成 {len(data)} 天的模拟数据，价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
    
    # 运行回测
    print("运行MACD策略回测...")
    result = strategy.backtest_strategy(data)
    
    if not result or len(result.get('trades', [])) < 2:
        print("回测失败或交易次数不足")
        return
    
    # 计算绩效指标
    performance = strategy.calculate_performance(result)
    
    # 生成报告
    report = strategy.generate_report(performance)
    print(report)
    
    # 显示交易详情
    trades = result['trades']
    print(f"\n=== 交易详情（前5笔） ===")
    for i in range(min(5, len(trades)//2)):
        buy_trade = trades[i*2]
        sell_trade = trades[i*2+1]
        pnl = (sell_trade['price'] - buy_trade['price']) * buy_trade['shares']
        
        print(f"交易 {i+1}:")
        print(f"  买入: {buy_trade['date'].strftime('%Y-%m-%d')} {buy_trade['price']:.2f} x {buy_trade['shares']}")
        print(f"  卖出: {sell_trade['date'].strftime('%Y-%m-%d')} {sell_trade['price']:.2f}")
        print(f"  盈亏: {pnl:,.2f} 元 ({((sell_trade['price']/buy_trade['price'])-1)*100:.2f}%)")
        print()
    
    # 保存结果
    import json
    with open('macd_backtest_result.json', 'w', encoding='utf-8') as f:
        json.dump({
            'strategy_params': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            'performance': performance,
            'total_trades': len(trades) // 2,
            'final_portfolio_value': result['final_value']
        }, f, indent=2, ensure_ascii=False)
    
    print("回测完成！结果已保存到 macd_backtest_result.json")
    print("\n=== 策略验证完成 ===")


if __name__ == "__main__":
    main()