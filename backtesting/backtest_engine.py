#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎 - 基于VeighNa回测框架
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import matplotlib.pyplot as plt
import seaborn as sns

from vnpy.app.cta_backtester import CtaBacktester
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import HistoryRequest, BarData
from vnpy.trader.constant import Exchange, Interval


class BacktestEngine:
    """
    回测引擎
    基于VeighNa CTA回测框架实现
    """
    
    def __init__(self, main_engine: MainEngine):
        """初始化"""
        self.main_engine = main_engine
        self.backtester = CtaBacktester(main_engine, main_engine.event_engine)
        
        # 回测结果
        self.results = {}
        self.df_results = pd.DataFrame()
        
    def run_backtest(
        self,
        strategy_name: str,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime,
        rate: float = 0.0003,
        slippage: float = 0.001,
        size: int = 1,
        pricetick: float = 0.01,
        capital: int = 1000000
    ) -> Dict:
        """运行回测"""
        try:
            # 设置回测参数
            setting = {
                "strategy_name": strategy_name,
                "vt_symbol": vt_symbol,
                "interval": interval,
                "start": start,
                "end": end,
                "rate": rate,
                "slippage": slippage,
                "size": size,
                "pricetick": pricetick,
                "capital": capital
            }
            
            # 运行回测
            self.backtester.set_parameters(
                vt_symbol=vt_symbol,
                interval=interval,
                start=start,
                end=end,
                rate=rate,
                slippage=slippage,
                size=size,
                pricetick=pricetick,
                capital=capital
            )
            
            # 添加策略
            self.backtester.add_strategy(strategy_name)
            
            # 运行回测
            self.backtester.run_backtesting()
            
            # 获取回测结果
            result = self.backtester.get_result_df()
            self.df_results = result
            
            # 计算绩效指标
            performance = self.calculate_performance(result)
            
            # 保存结果
            self.results[strategy_name] = {
                'setting': setting,
                'performance': performance,
                'trades': result.to_dict('records')
            }
            
            return performance
            
        except Exception as e:
            print(f"回测运行失败: {e}")
            return {}
    
    def calculate_performance(self, df_trades: pd.DataFrame) -> Dict:
        """计算绩效指标"""
        if df_trades.empty:
            return {}
        
        try:
            # 基本统计
            total_trades = len(df_trades)
            winning_trades = len(df_trades[df_trades['pnl'] > 0])
            losing_trades = len(df_trades[df_trades['pnl'] < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 盈亏统计
            total_pnl = df_trades['pnl'].sum()
            avg_pnl = df_trades['pnl'].mean()
            max_profit = df_trades['pnl'].max()
            max_loss = df_trades['pnl'].min()
            
            # 夏普比率 (简化计算)
            pnl_std = df_trades['pnl'].std()
            sharpe_ratio = avg_pnl / pnl_std if pnl_std > 0 else 0
            
            # 最大回撤
            cumulative_pnl = df_trades['pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            
            # 持仓时间统计
            if 'entry_time' in df_trades.columns and 'exit_time' in df_trades.columns:
                df_trades['holding_period'] = (df_trades['exit_time'] - df_trades['entry_time']).dt.days
                avg_holding_period = df_trades['holding_period'].mean()
            else:
                avg_holding_period = 0
            
            performance = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate * 100, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'max_profit': round(max_profit, 2),
                'max_loss': round(max_loss, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'avg_holding_period': round(avg_holding_period, 2)
            }
            
            return performance
            
        except Exception as e:
            print(f"计算绩效指标失败: {e}")
            return {}
    
    def generate_report(self, strategy_name: str) -> str:
        """生成回测报告"""
        if strategy_name not in self.results:
            return "策略回测结果不存在"
        
        result = self.results[strategy_name]
        performance = result['performance']
        
        # 创建报告
        report = f"""
=== MACD策略回测报告 ===
策略名称: {strategy_name}
回测期间: {result['setting']['start'].strftime('%Y-%m-%d')} 至 {result['setting']['end'].strftime('%Y-%m-%d')}

=== 绩效指标 ===
总交易次数: {performance['total_trades']}
盈利交易: {performance['winning_trades']}
亏损交易: {performance['losing_trades']}
胜率: {performance['win_rate']}%

总盈亏: {performance['total_pnl']:,.2f}
平均盈亏: {performance['avg_pnl']:,.2f}
最大盈利: {performance['max_profit']:,.2f}
最大亏损: {performance['max_loss']:,.2f}

夏普比率: {performance['sharpe_ratio']}
最大回撤: {performance['max_drawdown']:,.2f}
平均持仓天数: {performance['avg_holding_period']}

=== 策略参数 ===
标的: {result['setting']['vt_symbol']}
周期: {result['setting']['interval'].value}
手续费率: {result['setting']['rate'] * 100}%
滑点: {result['setting']['slippage'] * 100}%
初始资金: {result['setting']['capital']:,.0f}
"""
        
        return report
    
    def plot_performance(self, strategy_name: str, save_path: str = None):
        """绘制绩效图表"""
        if strategy_name not in self.results:
            print("策略回测结果不存在")
            return
        
        try:
            # 创建图表
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 累计收益曲线
            if not self.df_results.empty:
                cumulative_pnl = self.df_results['pnl'].cumsum()
                axes[0, 0].plot(cumulative_pnl.index, cumulative_pnl.values)
                axes[0, 0].set_title('累计收益曲线')
                axes[0, 0].set_xlabel('时间')
                axes[0, 0].set_ylabel('累计收益')
                axes[0, 0].grid(True)
            
            # 盈亏分布
            if 'pnl' in self.df_results.columns:
                axes[0, 1].hist(self.df_results['pnl'], bins=50, alpha=0.7)
                axes[0, 1].set_title('盈亏分布')
                axes[0, 1].set_xlabel('盈亏金额')
                axes[0, 1].set_ylabel('频次')
                axes[0, 1].grid(True)
            
            # 月度收益
            if not self.df_results.empty and 'datetime' in self.df_results.columns:
                monthly_pnl = self.df_results.groupby(
                    pd.Grouper(key='datetime', freq='M')
                )['pnl'].sum()
                axes[1, 0].bar(monthly_pnl.index.strftime('%Y-%m'), monthly_pnl.values)
                axes[1, 0].set_title('月度收益')
                axes[1, 0].set_xlabel('月份')
                axes[1, 0].set_ylabel('收益')
                axes[1, 0].tick_params(axis='x', rotation=45)
                axes[1, 0].grid(True)
            
            # 交易统计
            performance = self.results[strategy_name]['performance']
            stats_data = {
                '指标': ['胜率', '夏普比率', '最大回撤'],
                '数值': [performance['win_rate'], performance['sharpe_ratio'], performance['max_drawdown']]
            }
            stats_df = pd.DataFrame(stats_data)
            axes[1, 1].bar(stats_df['指标'], stats_df['数值'])
            axes[1, 1].set_title('关键指标')
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"图表已保存至: {save_path}")
            
            plt.show()
            
        except Exception as e:
            print(f"绘制图表失败: {e}")
    
    def save_results(self, file_path: str):
        """保存回测结果"""
        try:
            # 转换为可序列化的格式
            serializable_results = {}
            for strategy_name, result in self.results.items():
                # 转换datetime对象为字符串
                setting = result['setting'].copy()
                setting['start'] = setting['start'].strftime('%Y-%m-%d')
                setting['end'] = setting['end'].strftime('%Y-%m-%d')
                
                serializable_results[strategy_name] = {
                    'setting': setting,
                    'performance': result['performance']
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            
            print(f"回测结果已保存至: {file_path}")
            
        except Exception as e:
            print(f"保存回测结果失败: {e}")
    
    def load_results(self, file_path: str):
        """加载回测结果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换字符串为datetime对象
            for strategy_name, result in data.items():
                setting = result['setting']
                setting['start'] = datetime.strptime(setting['start'], '%Y-%m-%d')
                setting['end'] = datetime.strptime(setting['end'], '%Y-%m-%d')
            
            self.results = data
            print(f"回测结果已加载: {file_path}")
            
        except Exception as e:
            print(f"加载回测结果失败: {e}")