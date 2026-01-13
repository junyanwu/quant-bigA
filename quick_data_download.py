#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速下载A股数据 - 简化和稳定的版本
"""

import pandas as pd
import akshare as ak
import os
import time
from datetime import datetime

# 创建数据目录
DATA_PATH = './data'
os.makedirs(f"{DATA_PATH}/stocks", exist_ok=True)
os.makedirs(f"{DATA_PATH}/etfs", exist_ok=True)
os.makedirs(f"{DATA_PATH}/index", exist_ok=True)

def download_stock_data():
    """下载代表性股票数据"""
    print("📈 开始下载股票数据...")
    
    # 选择一些代表性的股票
    representative_stocks = [
        ('000001.SZ', '平安银行'),
        ('000002.SZ', '万科A'),
        ('600036.SH', '招商银行'),
        ('601318.SH', '中国平安'),
        ('600519.SH', '贵州茅台'),
        ('000858.SZ', '五粮液'),
        ('300750.SZ', '宁德时代'),
        ('002415.SZ', '海康威视'),
        ('600887.SH', '伊利股份'),
        ('601888.SH', '中国中免')
    ]
    
    success_count = 0
    for symbol, name in representative_stocks:
        try:
            code = symbol.split('.')[0]
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20200101", end_date="20241231", adjust="qfq")
            
            if not df.empty:
                # 检查列数并标准化列名
                if len(df.columns) == 12:
                    # 中文列名：['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
                    df.columns = ['date', 'code', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover']
                else:
                    # 备用列名
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover'][:len(df.columns)]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                # 保存为CSV
                file_path = f"{DATA_PATH}/stocks/{symbol}.csv"
                df.to_csv(file_path)
                success_count += 1
                print(f"✅ 成功下载 {symbol} ({name}) - {len(df)} 条记录")
            else:
                print(f"❌ {symbol} ({name}) 无数据")
                
        except Exception as e:
            print(f"❌ 下载 {symbol} ({name}) 失败: {e}")
    
    print(f"股票数据下载完成: {success_count}/{len(representative_stocks)} 成功")
    return success_count

def download_etf_data():
    """下载代表性ETF数据"""
    print("\n📊 开始下载ETF数据...")
    
    # 选择一些代表性的ETF
    representative_etfs = [
        ('510300.SH', '沪深300ETF'),
        ('510050.SH', '上证50ETF'),
        ('159915.SZ', '创业板ETF'),
        ('512100.SH', '中证1000ETF'),
        ('512880.SH', '券商ETF'),
        ('512690.SH', '酒ETF'),
        ('515000.SH', '科技ETF'),
        ('512760.SH', '芯片ETF'),
        ('512170.SH', '医疗ETF'),
        ('515030.SH', '新能源车ETF')
    ]
    
    success_count = 0
    for symbol, name in representative_etfs:
        try:
            code = symbol.split('.')[0]
            
            # 尝试ETF专用接口
            try:
                df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date="20200101", end_date="20241231", adjust="qfq")
            except:
                # 备用方法：使用股票接口
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20200101", end_date="20241231", adjust="qfq")
            
            if not df.empty:
                # 检查列数并标准化列名
                if len(df.columns) == 12:
                    # 中文列名：['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
                    df.columns = ['date', 'code', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover']
                else:
                    # 备用列名
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover'][:len(df.columns)]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                # 保存为CSV
                file_path = f"{DATA_PATH}/etfs/{symbol}.csv"
                df.to_csv(file_path)
                success_count += 1
                print(f"✅ 成功下载 {symbol} ({name}) - {len(df)} 条记录")
            else:
                print(f"❌ {symbol} ({name}) 无数据")
                
        except Exception as e:
            print(f"❌ 下载 {symbol} ({name}) 失败: {e}")
    
    print(f"ETF数据下载完成: {success_count}/{len(representative_etfs)} 成功")
    return success_count

def download_index_data():
    """下载主要指数数据"""
    print("\n📈 开始下载指数数据...")
    
    indices = [
        ('000001.SH', '上证指数'),
        ('000300.SH', '沪深300'),
        ('000905.SH', '中证500'),
        ('399001.SZ', '深证成指'),
        ('399006.SZ', '创业板指')
    ]
    
    success_count = 0
    for symbol, name in indices:
        try:
            code = symbol.split('.')[0]
            df = ak.index_zh_a_hist(symbol=code, period="daily", start_date="20200101", end_date="20241231")
            
            if not df.empty:
                # 检查指数数据的实际列数
                if len(df.columns) == 11:
                    # 中文列名：['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover']
                elif len(df.columns) == 7:
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
                else:
                    # 备用列名
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                                 'change_percent', 'change_amount', 'turnover'][:len(df.columns)]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                # 保存为CSV
                file_path = f"{DATA_PATH}/index/{symbol}.csv"
                df.to_csv(file_path)
                success_count += 1
                print(f"✅ 成功下载 {symbol} ({name}) - {len(df)} 条记录")
            else:
                print(f"❌ {symbol} ({name}) 无数据")
                
        except Exception as e:
            print(f"❌ 下载 {symbol} ({name}) 失败: {e}")
    
    print(f"指数数据下载完成: {success_count}/{len(indices)} 成功")
    return success_count

def main():
    """主函数"""
    print("🚀 A股数据快速下载开始...")
    print("=" * 50)
    
    start_time = time.time()
    
    # 下载股票数据
    stock_success = download_stock_data()
    
    # 下载ETF数据
    etf_success = download_etf_data()
    
    # 下载指数数据
    index_success = download_index_data()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    print("📊 下载完成报告")
    print("=" * 50)
    print(f"股票数据: {stock_success} 个成功")
    print(f"ETF数据: {etf_success} 个成功")
    print(f"指数数据: {index_success} 个成功")
    print(f"总计耗时: {elapsed_time:.2f} 秒")
    print(f"数据保存路径: {DATA_PATH}")
    
    # 显示文件结构
    print("\n📁 数据文件结构:")
    for data_type in ['stocks', 'etfs', 'index']:
        dir_path = f"{DATA_PATH}/{data_type}"
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]
            print(f"  {data_type}/: {len(files)} 个CSV文件")
    
    print("\n✅ 数据下载完成！可以开始进行回测分析。")

if __name__ == "__main__":
    main()