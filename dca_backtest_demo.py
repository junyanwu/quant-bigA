"""
定投策略回测演示
测试不同指数的定投收益情况
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.dca_strategy import DCAStrategy
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def generate_mock_index_data():
    """
    生成模拟的指数数据（由于实际数据获取需要网络，这里使用模拟数据）
    """
    # 设置时间范围：2015-2024年
    dates = pd.date_range('2015-01-01', '2024-12-31', freq='D')
    
    # 只保留交易日（周一至周五）
    dates = dates[dates.dayofweek < 5]
    
    price_data = {}
    
    # 1. 沪深300指数 (相对稳定，代表大盘)
    np.random.seed(42)
    base_300 = 3000
    returns_300 = np.random.normal(0.0003, 0.015, len(dates))  # 年化约8%
    prices_300 = base_300 * np.cumprod(1 + returns_300)
    price_data['沪深300'] = pd.Series(prices_300, index=dates)
    
    # 2. 创业板指数 (高波动，高风险高收益)
    np.random.seed(43)
    base_cyb = 1500
    returns_cyb = np.random.normal(0.0005, 0.025, len(dates))  # 年化约12%
    prices_cyb = base_cyb * np.cumprod(1 + returns_cyb)
    price_data['创业板指'] = pd.Series(prices_cyb, index=dates)
    
    # 3. 中证500指数 (中小盘代表)
    np.random.seed(44)
    base_500 = 5000
    returns_500 = np.random.normal(0.0004, 0.018, len(dates))  # 年化约10%
    prices_500 = base_500 * np.cumprod(1 + returns_500)
    price_data['中证500'] = pd.Series(prices_500, index=dates)
    
    # 4. 上证50指数 (大盘蓝筹)
    np.random.seed(45)
    base_50 = 2000
    returns_50 = np.random.normal(0.00025, 0.012, len(dates))  # 年化约6%
    prices_50 = base_50 * np.cumprod(1 + returns_50)
    price_data['上证50'] = pd.Series(prices_50, index=dates)
    
    # 5. 科创50指数 (科技创新)
    np.random.seed(46)
    base_kc = 1000
    returns_kc = np.random.normal(0.0006, 0.022, len(dates))  # 年化约15%
    prices_kc = base_kc * np.cumprod(1 + returns_kc)
    price_data['科创50'] = pd.Series(prices_kc, index=dates)
    
    return price_data

def run_dca_backtest():
    """运行定投回测"""
    print("🚀 开始定投策略回测...")
    
    # 生成模拟数据
    print("📊 生成指数数据...")
    price_data = generate_mock_index_data()
    
    # 创建定投策略实例
    dca_strategy = DCAStrategy(
        initial_capital=100000,  # 10万元初始资金
        monthly_investment=5000   # 每月定投5000元
    )
    
    # 设置回测期间
    start_date = '2018-01-01'
    end_date = '2024-12-31'
    
    print(f"📅 回测期间: {start_date} 至 {end_date}")
    print(f"💰 定投设置: 每月{dca_strategy.monthly_investment:,}元")
    
    # 运行回测
    print("\n🔄 计算各指数定投收益...")
    results_df = dca_strategy.backtest_multiple_indices(price_data, start_date, end_date)
    
    # 生成报告
    dca_strategy.generate_report(results_df)
    
    # 绘制图表
    print("\n📈 生成可视化图表...")
    dca_strategy.plot_results(results_df, price_data)
    
    return results_df, price_data

def analyze_dca_performance(results_df):
    """深入分析定投表现"""
    print("\n" + "=" * 60)
    print("           定投策略深度分析")
    print("=" * 60)
    
    # 风险调整后收益分析
    print("\n📊 风险收益特征:")
    for _, row in results_df.iterrows():
        volatility = row['total_return'] / row['investment_months'] * 12  # 简化波动率
        sharpe_ratio = row['annual_return'] / volatility if volatility > 0 else 0
        print(f"   {row['index']}: 年化{row['annual_return']:.1f}% | 波动率{volatility:.1f}% | 夏普比率{sharpe_ratio:.2f}")
    
    # 定投优势分析
    print(f"\n💡 定投策略优势分析:")
    
    # 计算定投在熊市中的表现
    bear_market_performance = results_df.sort_values('total_return').head(2)
    print(f"   熊市中表现最好的指数:")
    for _, row in bear_market_performance.iterrows():
        print(f"     - {row['index']}: 定投vs一次性 +{row['vs_lump_sum']:,.0f}元")
    
    # 投资纪律分析
    total_months = results_df['investment_months'].max()
    print(f"\n⏰ 投资纪律:")
    print(f"   坚持定投{total_months}个月")
    print(f"   总投入金额: {results_df['total_invested'].max():,.0f}元")
    
    # 定投适合人群
    print(f"\n👥 适合人群:")
    print(f"   ✅ 上班族 - 每月固定收入")
    print(f"   ✅ 投资新手 - 无需择时")
    print(f"   ✅ 长期投资者 - 时间换空间")
    print(f"   ✅ 风险厌恶者 - 平滑波动")

def compare_different_strategies():
    """比较不同定投策略"""
    print("\n" + "=" * 60)
    print("           不同定投策略对比")
    print("=" * 60)
    
    # 生成数据
    price_data = generate_mock_index_data()
    
    # 测试不同定投金额
    strategies = [
        ("保守型", 3000),
        ("平衡型", 5000), 
        ("积极型", 8000)
    ]
    
    strategy_results = []
    
    for strategy_name, monthly_amount in strategies:
        dca = DCAStrategy(monthly_investment=monthly_amount)
        results = dca.backtest_multiple_indices(price_data, '2018-01-01', '2024-12-31')
        
        # 取沪深300的结果作为代表
        hs300_result = results[results['index'] == '沪深300'].iloc[0]
        strategy_results.append({
            'strategy': strategy_name,
            'monthly_amount': monthly_amount,
            'total_return': hs300_result['total_return'],
            'annual_return': hs300_result['annual_return'],
            'final_value': hs300_result['final_value']
        })
    
    print("\n💰 不同定投金额策略对比 (以沪深300为例):")
    for result in strategy_results:
        print(f"   {result['strategy']} ({result['monthly_amount']:,}元/月):")
        print(f"      总收益: {result['total_return']:.1f}%")
        print(f"      年化收益: {result['annual_return']:.1f}%")
        print(f"      最终价值: {result['final_value']:,.0f}元")
        print()

if __name__ == "__main__":
    print("🎯 A股指数定投策略回测系统")
    print("=" * 60)
    
    try:
        # 运行主要回测
        results_df, price_data = run_dca_backtest()
        
        # 深度分析
        analyze_dca_performance(results_df)
        
        # 策略对比
        compare_different_strategies()
        
        print("\n" + "🎉 回测完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()