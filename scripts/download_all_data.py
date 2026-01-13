#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股所有股票和ETF数据批量下载脚本
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetcher import AShareDataFetcher
from config.config import DATA_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_complete_dataset():
    """下载完整的A股数据集"""
    print("🚀 开始下载A股所有股票和ETF数据")
    print("=" * 60)
    
    # 创建数据获取器
    fetcher = AShareDataFetcher()
    
    # 显示下载配置
    print(f"📊 下载配置:")
    print(f"   数据路径: {DATA_CONFIG['data_path']}")
    print(f"   时间范围: {DATA_CONFIG['start_date']} 至 {DATA_CONFIG['end_date']}")
    print(f"   并行线程: {DATA_CONFIG.get('max_workers', 10)}")
    
    # 检查数据目录
    data_path = DATA_CONFIG['data_path']
    if not os.path.exists(data_path):
        os.makedirs(data_path)
        print(f"✅ 创建数据目录: {data_path}")
    
    # 开始下载
    start_time = time.time()
    
    try:
        print("\n📥 开始批量下载数据...")
        results = fetcher.download_all_data(max_workers=DATA_CONFIG.get('max_workers', 10))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 显示下载结果
        print("\n" + "=" * 60)
        print("           数据下载完成")
        print("=" * 60)
        
        print(f"\n📊 下载统计:")
        print(f"   总耗时: {duration:.2f} 秒 ({duration/60:.1f} 分钟)")
        print(f"   成功股票: {len(results['stocks'])} 只")
        print(f"   成功ETF: {len(results['etfs'])} 只")
        print(f"   失败标的: {len(results['failed'])} 个")
        
        if results['failed']:
            print(f"\n⚠️  失败标的列表:")
            for symbol in results['failed'][:10]:  # 只显示前10个
                print(f"   - {symbol}")
            if len(results['failed']) > 10:
                print(f"   ... 还有 {len(results['failed']) - 10} 个失败标的")
        
        # 显示可用数据
        available = fetcher.get_available_symbols()
        print(f"\n💾 本地数据统计:")
        print(f"   股票数据: {len(available['stocks'])} 个文件")
        print(f"   ETF数据: {len(available['etfs'])} 个文件")
        print(f"   指数数据: {len(available['index'])} 个文件")
        
        # 保存下载摘要
        summary_file = os.path.join(data_path, 'download_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("A股数据下载摘要\n")
            f.write("=" * 50 + "\n")
            f.write(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据范围: {DATA_CONFIG['start_date']} 至 {DATA_CONFIG['end_date']}\n")
            f.write(f"成功股票: {len(results['stocks'])} 只\n")
            f.write(f"成功ETF: {len(results['etfs'])} 只\n")
            f.write(f"失败标的: {len(results['failed'])} 个\n")
            f.write(f"总耗时: {duration:.2f} 秒\n\n")
            
            f.write("成功下载的股票(前20只):\n")
            for symbol in results['stocks'][:20]:
                f.write(f"  {symbol}\n")
            
            f.write("\n成功下载的ETF(前20只):\n")
            for symbol in results['etfs'][:20]:
                f.write(f"  {symbol}\n")
        
        print(f"\n📄 下载摘要已保存至: {summary_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"下载过程中出现错误: {e}")
        print(f"❌ 下载失败: {e}")
        return None

def check_data_quality():
    """检查数据质量"""
    print("\n" + "=" * 60)
    print("           数据质量检查")
    print("=" * 60)
    
    fetcher = AShareDataFetcher()
    available = fetcher.get_available_symbols()
    
    # 随机抽样检查数据完整性
    sample_symbols = available['stocks'][:5] + available['etfs'][:3] + available['index'][:2]
    
    quality_report = []
    
    for symbol in sample_symbols:
        try:
            if symbol in available['stocks']:
                data = fetcher.load_data(symbol, 'stock')
                symbol_type = '股票'
            elif symbol in available['etfs']:
                data = fetcher.load_data(symbol, 'etf')
                symbol_type = 'ETF'
            else:
                data = fetcher.load_data(symbol, 'index')
                symbol_type = '指数'
            
            if data is not None and not data.empty:
                quality_report.append({
                    'symbol': symbol,
                    'type': symbol_type,
                    'records': len(data),
                    'start_date': data.index[0].strftime('%Y-%m-%d'),
                    'end_date': data.index[-1].strftime('%Y-%m-%d'),
                    'status': '✅ 正常'
                })
            else:
                quality_report.append({
                    'symbol': symbol,
                    'type': symbol_type,
                    'records': 0,
                    'start_date': 'N/A',
                    'end_date': 'N/A',
                    'status': '❌ 异常'
                })
                
        except Exception as e:
            quality_report.append({
                'symbol': symbol,
                'type': symbol_type,
                'records': 0,
                'start_date': 'N/A',
                'end_date': 'N/A',
                'status': f'❌ 错误: {str(e)}'
            })
    
    # 显示质量报告
    print("\n🔍 数据质量抽样检查:")
    for report in quality_report:
        print(f"   {report['symbol']} ({report['type']}): {report['status']}")
        if report['records'] > 0:
            print(f"       记录数: {report['records']}, 时间范围: {report['start_date']} 至 {report['end_date']}")
    
    return quality_report

def main():
    """主函数"""
    print("🎯 A股数据批量下载工具")
    print("=" * 60)
    
    # 下载数据
    results = download_complete_dataset()
    
    if results:
        # 检查数据质量
        quality_report = check_data_quality()
        
        # 生成使用建议
        print("\n" + "=" * 60)
        print("           使用建议")
        print("=" * 60)
        
        print("\n💡 数据使用说明:")
        print("   1. 回测时可使用 load_data() 方法加载本地数据")
        print("   2. 数据文件路径: ./data/stocks/ 和 ./data/etfs/")
        print("   3. 支持股票、ETF、指数三种类型数据")
        print("   4. 数据已包含复权价格，可直接用于回测")
        
        print("\n🚀 下一步操作:")
        print("   python run.py --mode backtest     # 运行回测")
        print("   python scripts/run_backtest.py   # 运行回测脚本")
        
        print("\n✅ 数据下载完成，可以开始回测了！")
    else:
        print("\n❌ 数据下载失败，请检查网络连接和数据源配置")

if __name__ == "__main__":
    main()