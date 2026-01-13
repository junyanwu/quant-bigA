"""
简化的定投策略测试
测试不同指数的定投收益情况
"""

import math
import random
from datetime import datetime, timedelta

def generate_simple_index_data():
    """生成简化的指数数据"""
    # 模拟5个主要A股指数的历史数据（2018-2024）
    indices = {
        '沪深300': {'base': 3000, 'volatility': 0.015, 'trend': 0.0003},  # 大盘蓝筹
        '创业板指': {'base': 1500, 'volatility': 0.025, 'trend': 0.0005},  # 高成长
        '中证500': {'base': 5000, 'volatility': 0.018, 'trend': 0.0004},  # 中小盘
        '上证50': {'base': 2000, 'volatility': 0.012, 'trend': 0.00025},  # 大盘价值
        '科创50': {'base': 1000, 'volatility': 0.022, 'trend': 0.0006}   # 科技创新
    }
    
    # 生成84个月的数据（2018-2024）
    monthly_data = {}
    for name, params in indices.items():
        prices = []
        current_price = params['base']
        
        for month in range(84):
            # 每月价格波动
            monthly_return = random.gauss(params['trend'] * 21, params['volatility'] / math.sqrt(21))
            current_price *= (1 + monthly_return)
            prices.append(current_price)
        
        monthly_data[name] = prices
    
    return monthly_data

def dca_strategy_simple(index_prices, monthly_investment=5000, start_month=0):
    """简化的定投策略计算"""
    total_invested = 0
    total_shares = 0
    investment_records = []
    
    # 每月定投
    for month in range(start_month, len(index_prices)):
        price = index_prices[month]
        shares = monthly_investment / price
        total_invested += monthly_investment
        total_shares += shares
        
        current_value = total_shares * price
        investment_records.append({
            'month': month + 1,
            'price': price,
            'shares': shares,
            'total_invested': total_invested,
            'current_value': current_value
        })
    
    # 计算最终结果
    if not investment_records:
        return None
        
    final_record = investment_records[-1]
    final_value = final_record['current_value']
    total_return = (final_value - total_invested) / total_invested * 100
    
    # 计算一次性投资对比
    lump_sum_value = (100000 / index_prices[0]) * index_prices[-1]
    
    return {
        'total_invested': total_invested,
        'final_value': final_value,
        'total_return': total_return,
        'annual_return': total_return / (len(index_prices) / 12),  # 简化年化计算
        'lump_sum_value': lump_sum_value,
        'vs_lump_sum': final_value - lump_sum_value
    }

def run_dca_analysis():
    """运行定投分析"""
    print("🎯 A股指数定投策略回测分析")
    print("=" * 60)
    
    # 生成数据
    print("📊 生成指数数据...")
    monthly_data = generate_simple_index_data()
    
    # 运行定投策略
    print("\n💰 定投策略设置:")
    print("   初始资金: 100,000元")
    print("   每月定投: 5,000元")
    print("   回测期间: 2018年1月 - 2024年12月 (84个月)")
    
    results = {}
    for index_name, prices in monthly_data.items():
        result = dca_strategy_simple(prices)
        if result:
            results[index_name] = result
    
    # 输出结果
    print("\n" + "=" * 60)
    print("           定投策略回测结果")
    print("=" * 60)
    
    # 按总收益率排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]['total_return'], reverse=True)
    
    print("\n🏆 收益率排名:")
    for i, (index_name, result) in enumerate(sorted_results, 1):
        print(f"   {i}. {index_name}: {result['total_return']:.1f}%")
    
    print("\n📊 详细数据:")
    for index_name, result in sorted_results:
        print(f"\n   📈 {index_name}:")
        print(f"      总投入: {result['total_invested']:,.0f}元")
        print(f"      最终价值: {result['final_value']:,.0f}元")
        print(f"      总收益率: {result['total_return']:.1f}%")
        print(f"      年化收益率: {result['annual_return']:.1f}%")
        print(f"      定投vs一次性: {result['vs_lump_sum']:,.0f}元")
    
    # 统计分析
    print("\n" + "=" * 60)
    print("           统计分析")
    print("=" * 60)
    
    total_returns = [r['total_return'] for r in results.values()]
    avg_return = sum(total_returns) / len(total_returns)
    max_return = max(total_returns)
    min_return = min(total_returns)
    
    print(f"\n📈 整体表现:")
    print(f"   平均收益率: {avg_return:.1f}%")
    print(f"   最高收益率: {max_return:.1f}% ({sorted_results[0][0]})")
    print(f"   最低收益率: {min_return:.1f}% ({sorted_results[-1][0]})")
    
    # 定投优势分析
    positive_count = sum(1 for r in results.values() if r['vs_lump_sum'] > 0)
    total_count = len(results)
    
    print(f"\n💡 定投策略优势:")
    print(f"   定投优于一次性投资的比例: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}%)")
    
    if positive_count > total_count / 2:
        print("   ✅ 定投策略在多数情况下优于一次性投资")
    else:
        print("   ⚠️  一次性投资在多数情况下表现更好")
    
    # 投资建议
    print(f"\n🎯 投资建议:")
    best_index = sorted_results[0][0]
    worst_index = sorted_results[-1][0]
    
    print(f"   推荐指数: {best_index} (历史表现最佳)")
    print(f"   谨慎投资: {worst_index} (历史表现较差)")
    print(f"   适合人群: 上班族、投资新手、长期投资者")
    
    print("\n" + "=" * 60)
    print("🎉 回测分析完成!")
    
    return results

def compare_different_periods():
    """比较不同定投期间的表现"""
    print("\n" + "=" * 60)
    print("           不同定投期间对比")
    print("=" * 60)
    
    monthly_data = generate_simple_index_data()
    
    # 测试不同定投期间
    periods = [
        ("短期(3年)", 36),
        ("中期(5年)", 60), 
        ("长期(7年)", 84)
    ]
    
    print("\n以沪深300为例，比较不同定投期间的表现:")
    hs300_prices = monthly_data['沪深300']
    
    for period_name, months in periods:
        if months <= len(hs300_prices):
            result = dca_strategy_simple(hs300_prices[:months])
            if result:
                print(f"\n   {period_name}:")
                print(f"      总收益率: {result['total_return']:.1f}%")
                print(f"      年化收益率: {result['annual_return']:.1f}%")
                print(f"      定投优势: {result['vs_lump_sum']:,.0f}元")

if __name__ == "__main__":
    # 运行主要分析
    results = run_dca_analysis()
    
    # 比较不同期间
    compare_different_periods()
    
    print("\n" + "=" * 60)
    print("💡 定投策略核心优势:")
    print("   1. 分散投资时点，降低择时风险")
    print("   2. 平滑市场波动，适合震荡市")
    print("   3. 培养投资纪律，避免情绪化操作")
    print("   4. 适合每月有固定收入的投资者")
    print("=" * 60)