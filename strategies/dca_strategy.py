"""
定投策略 (Dollar-Cost Averaging Strategy)
定期定额投资不同指数的策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class DCAStrategy:
    """
    定投策略类
    """
    
    def __init__(self, initial_capital: float = 100000, monthly_investment: float = 10000):
        """
        初始化定投策略
        
        Args:
            initial_capital: 初始资金
            monthly_investment: 每月定投金额
        """
        self.initial_capital = initial_capital
        self.monthly_investment = monthly_investment
        self.results = {}
        
    def calculate_dca_returns(self, prices: pd.Series, start_date: str, end_date: str) -> Dict:
        """
        计算定投收益
        
        Args:
            prices: 价格序列
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            定投结果字典
        """
        # 筛选日期范围
        prices = prices.loc[start_date:end_date]
        if len(prices) == 0:
            return {}
            
        # 生成每月定投日期（每月第一个交易日）
        monthly_dates = self._generate_monthly_dates(prices.index, start_date, end_date)
        
        # 计算定投收益
        total_invested = 0
        total_shares = 0
        investment_records = []
        
        for date in monthly_dates:
            if date in prices.index:
                price = prices.loc[date]
                shares = self.monthly_investment / price
                total_invested += self.monthly_investment
                total_shares += shares
                
                investment_records.append({
                    'date': date,
                    'price': price,
                    'shares': shares,
                    'amount': self.monthly_investment,
                    'total_invested': total_invested,
                    'total_shares': total_shares,
                    'current_value': total_shares * price
                })
        
        # 计算最终结果
        if len(investment_records) == 0:
            return {}
            
        final_record = investment_records[-1]
        final_price = prices.iloc[-1]
        final_value = total_shares * final_price
        
        # 计算一次性投资对比
        lump_sum_shares = self.initial_capital / prices.iloc[0]
        lump_sum_value = lump_sum_shares * final_price
        
        result = {
            'total_invested': total_invested,
            'total_shares': total_shares,
            'final_value': final_value,
            'total_return': (final_value - total_invested) / total_invested * 100,
            'annual_return': self._calculate_annual_return(total_invested, final_value, start_date, end_date),
            'investment_months': len(monthly_dates),
            'investment_records': investment_records,
            'lump_sum_value': lump_sum_value,
            'lump_sum_return': (lump_sum_value - self.initial_capital) / self.initial_capital * 100,
            'vs_lump_sum': final_value - lump_sum_value
        }
        
        return result
    
    def _generate_monthly_dates(self, all_dates: pd.DatetimeIndex, start_date: str, end_date: str) -> List:
        """生成每月定投日期"""
        monthly_dates = []
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        while current_date <= end_date:
            # 找到该月第一个交易日
            month_start = current_date.replace(day=1)
            month_dates = all_dates[all_dates >= month_start]
            if len(month_dates) > 0:
                first_trading_day = month_dates[0]
                if first_trading_day <= end_date:
                    monthly_dates.append(first_trading_day)
            
            # 移动到下个月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return monthly_dates
    
    def _calculate_annual_return(self, total_invested: float, final_value: float, 
                               start_date: str, end_date: str) -> float:
        """计算年化收益率"""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        years = (end - start).days / 365.25
        
        if years <= 0:
            return 0
        
        # 使用内部收益率近似计算年化收益率
        annual_return = ((final_value / total_invested) ** (1 / years) - 1) * 100
        return annual_return
    
    def backtest_multiple_indices(self, price_data: Dict[str, pd.Series], 
                                 start_date: str, end_date: str) -> pd.DataFrame:
        """
        回测多个指数的定投收益
        
        Args:
            price_data: 各指数价格数据字典
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果DataFrame
        """
        results = []
        
        for index_name, prices in price_data.items():
            result = self.calculate_dca_returns(prices, start_date, end_date)
            if result:
                result['index'] = index_name
                results.append(result)
        
        return pd.DataFrame(results)
    
    def plot_results(self, results_df: pd.DataFrame, price_data: Dict[str, pd.Series]):
        """绘制回测结果图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 总收益率对比
        axes[0, 0].bar(results_df['index'], results_df['total_return'])
        axes[0, 0].set_title('各指数定投总收益率对比')
        axes[0, 0].set_ylabel('总收益率 (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 年化收益率对比
        axes[0, 1].bar(results_df['index'], results_df['annual_return'])
        axes[0, 1].set_title('各指数定投年化收益率对比')
        axes[0, 1].set_ylabel('年化收益率 (%)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 定投vs一次性投资
        axes[1, 0].bar(results_df['index'], results_df['vs_lump_sum'])
        axes[1, 0].set_title('定投vs一次性投资收益差（定投-一次性）')
        axes[1, 0].set_ylabel('收益差 (元)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 价格走势
        for index_name, prices in price_data.items():
            if index_name in results_df['index'].values:
                axes[1, 1].plot(prices.index, prices.values, label=index_name, alpha=0.7)
        axes[1, 1].set_title('各指数价格走势')
        axes[1, 1].set_ylabel('价格')
        axes[1, 1].legend()
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
        
        return fig
    
    def generate_report(self, results_df: pd.DataFrame):
        """生成回测报告"""
        print("=" * 60)
        print("           定投策略回测报告")
        print("=" * 60)
        
        print(f"\n📊 回测概况:")
        print(f"   初始资金: {self.initial_capital:,}元")
        print(f"   每月定投: {self.monthly_investment:,}元")
        print(f"   回测指数数量: {len(results_df)}")
        
        print(f"\n🏆 收益率排名:")
        ranked_results = results_df.sort_values('total_return', ascending=False)
        for i, (_, row) in enumerate(ranked_results.iterrows(), 1):
            print(f"   {i}. {row['index']}: 总收益{row['total_return']:.2f}% | 年化{row['annual_return']:.2f}%")
        
        print(f"\n📈 详细数据:")
        for _, row in results_df.iterrows():
            print(f"\n   {row['index']}:")
            print(f"      总投入: {row['total_invested']:,.0f}元")
            print(f"      最终价值: {row['final_value']:,.0f}元")
            print(f"      总收益率: {row['total_return']:.2f}%")
            print(f"      年化收益率: {row['annual_return']:.2f}%")
            print(f"      定投vs一次性: {row['vs_lump_sum']:,.0f}元")
            
        best_index = ranked_results.iloc[0]
        worst_index = ranked_results.iloc[-1]
        
        print(f"\n💡 关键发现:")
        print(f"   最佳表现: {best_index['index']} (总收益{best_index['total_return']:.2f}%)")
        print(f"   最差表现: {worst_index['index']} (总收益{worst_index['total_return']:.2f}%)")
        print(f"   平均收益率: {results_df['total_return'].mean():.2f}%")
        
        # 定投优势分析
        positive_count = len(results_df[results_df['vs_lump_sum'] > 0])
        total_count = len(results_df)
        print(f"   定投优于一次性投资的比例: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}%)")
        
        print("\n" + "=" * 60)