#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整A股数据批量下载脚本
下载所有A股股票、ETF和指数数据，支持断点续传
"""

import pandas as pd
import akshare as ak
import os
import time
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_data_download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据配置
DATA_CONFIG = {
    'data_path': './data',
    'start_date': '20200101',  # 从2020年开始下载
    'end_date': datetime.now().strftime('%Y%m%d'),
    'max_workers': 6,  # 并发线程数
    'batch_size': 50   # 每批下载数量
}

class CompleteDataDownloader:
    """完整数据下载器"""
    
    def __init__(self):
        self.data_path = DATA_CONFIG['data_path']
        self.start_date = DATA_CONFIG['start_date']
        self.end_date = DATA_CONFIG['end_date']
        self.max_workers = DATA_CONFIG['max_workers']
        self.batch_size = DATA_CONFIG['batch_size']
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'stocks'), exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'etfs'), exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'index'), exist_ok=True)
        
    def get_all_stocks(self) -> list:
        """获取所有A股股票列表"""
        try:
            stock_list = ak.stock_info_a_code_name()
            stocks = []
            
            for _, row in stock_list.iterrows():
                code = row['code']
                name = row['name']
                exchange = 'SH' if code.startswith(('6', '900', '688')) else 'SZ'
                symbol = f"{code}.{exchange}"
                
                stocks.append({
                    'symbol': symbol,
                    'code': code,
                    'name': name,
                    'exchange': exchange,
                    'type': 'stock'
                })
            
            logger.info(f"获取到 {len(stocks)} 只股票")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_all_etfs(self) -> list:
        """获取所有ETF列表"""
        try:
            etf_list = ak.fund_etf_spot_em()
            etfs = []
            
            for _, row in etf_list.iterrows():
                code = row['代码']
                name = row['名称']
                exchange = 'SH' if code.startswith('51') else 'SZ'
                symbol = f"{code}.{exchange}"
                
                etfs.append({
                    'symbol': symbol,
                    'code': code,
                    'name': name,
                    'exchange': exchange,
                    'type': 'etf'
                })
            
            logger.info(f"获取到 {len(etfs)} 只ETF")
            return etfs
            
        except Exception as e:
            logger.error(f"获取ETF列表失败: {e}")
            return []
    
    def download_single_symbol(self, symbol_info: dict) -> bool:
        """下载单个标的的历史数据"""
        symbol = symbol_info['symbol']
        code = symbol_info['code']
        name = symbol_info['name']
        symbol_type = symbol_info['type']
        
        try:
            # 检查文件是否已存在
            if symbol_type == 'stock':
                file_path = os.path.join(self.data_path, 'stocks', f"{symbol}.csv")
            else:
                file_path = os.path.join(self.data_path, 'etfs', f"{symbol}.csv")
                
            if os.path.exists(file_path):
                logger.info(f"{symbol} ({name}) 数据已存在，跳过")
                return True
            
            # 获取历史数据
            if symbol_type == 'stock':
                df = ak.stock_zh_a_hist(
                    symbol=code, 
                    period="daily", 
                    start_date=self.start_date, 
                    end_date=self.end_date, 
                    adjust="qfq"
                )
            else:
                # 尝试ETF专用接口
                try:
                    df = ak.fund_etf_hist_em(
                        symbol=code, 
                        period="daily", 
                        start_date=self.start_date, 
                        end_date=self.end_date, 
                        adjust="qfq"
                    )
                except:
                    # 备用方法：使用股票接口
                    df = ak.stock_zh_a_hist(
                        symbol=code, 
                        period="daily", 
                        start_date=self.start_date, 
                        end_date=self.end_date, 
                        adjust="qfq"
                    )
            
            if df.empty:
                logger.warning(f"{symbol} ({name}) 无数据")
                return False
            
            # 标准化列名
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
            df.to_csv(file_path)
            
            logger.info(f"✅ 成功下载 {symbol} ({name}) - {len(df)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"❌ 下载 {symbol} ({name}) 失败: {e}")
            return False
    
    def download_in_batches(self, symbols: list, batch_name: str) -> dict:
        """分批下载数据"""
        total_symbols = len(symbols)
        results = {'success': 0, 'failed': 0}
        
        logger.info(f"开始下载{batch_name}，共 {total_symbols} 个标的")
        
        for i in range(0, total_symbols, self.batch_size):
            batch = symbols[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total_symbols + self.batch_size - 1) // self.batch_size
            
            logger.info(f"下载批次 {batch_num}/{total_batches}，本批 {len(batch)} 个标的")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_single_symbol, symbol): symbol for symbol in batch}
                
                for future in as_completed(futures):
                    symbol_info = futures[future]
                    try:
                        if future.result():
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                    except Exception as e:
                        logger.error(f"下载任务异常: {e}")
                        results['failed'] += 1
            
            # 批次间暂停，避免API限制
            if i + self.batch_size < total_symbols:
                logger.info("批次完成，暂停5秒...")
                time.sleep(5)
        
        return results
    
    def download_main_indices(self):
        """下载主要指数数据"""
        indices = [
            {'symbol': '000001.SH', 'name': '上证指数'},
            {'symbol': '000300.SH', 'name': '沪深300'},
            {'symbol': '000905.SH', 'name': '中证500'},
            {'symbol': '399001.SZ', 'name': '深证成指'},
            {'symbol': '399006.SZ', 'name': '创业板指'},
            {'symbol': '399005.SZ', 'name': '中小板指'},
            {'symbol': '000016.SH', 'name': '上证50'},
            {'symbol': '000688.SH', 'name': '科创50'}
        ]
        
        logger.info("开始下载主要指数数据...")
        
        for index in indices:
            try:
                symbol = index['symbol']
                name = index['name']
                code = symbol.split('.')[0]
                
                file_path = os.path.join(self.data_path, 'index', f"{symbol}.csv")
                if os.path.exists(file_path):
                    logger.info(f"{symbol} ({name}) 数据已存在，跳过")
                    continue
                
                df = ak.index_zh_a_hist(
                    symbol=code, 
                    period="daily", 
                    start_date=self.start_date, 
                    end_date=self.end_date
                )
                
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
                    
                    df.to_csv(file_path)
                    logger.info(f"✅ 成功下载指数 {symbol} ({name}) - {len(df)} 条记录")
                
            except Exception as e:
                logger.error(f"❌ 下载指数 {symbol} 失败: {e}")
    
    def run_download(self):
        """运行批量下载"""
        start_time = time.time()
        
        logger.info("🚀 开始完整A股数据批量下载...")
        logger.info(f"数据路径: {self.data_path}")
        logger.info(f"时间范围: {self.start_date} 至 {self.end_date}")
        
        # 获取股票和ETF列表
        stocks = self.get_all_stocks()
        etfs = self.get_all_etfs()
        
        total_symbols = len(stocks) + len(etfs)
        logger.info(f"总计需要下载: {total_symbols} 个标的 (股票: {len(stocks)}, ETF: {len(etfs)})")
        
        if total_symbols == 0:
            logger.info("无数据可下载！")
            return
        
        # 分批下载股票
        if stocks:
            stock_results = self.download_in_batches(stocks, "股票")
        else:
            stock_results = {'success': 0, 'failed': 0}
        
        # 分批下载ETF
        if etfs:
            etf_results = self.download_in_batches(etfs, "ETF")
        else:
            etf_results = {'success': 0, 'failed': 0}
        
        # 下载指数数据
        self.download_main_indices()
        
        # 生成下载报告
        elapsed_time = time.time() - start_time
        self.generate_report(stock_results, etf_results, elapsed_time)
    
    def generate_report(self, stock_results: dict, etf_results: dict, elapsed_time: float):
        """生成下载报告"""
        report = {
            'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_time': f"{elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)",
            'stocks': {
                'success': stock_results['success'],
                'failed': stock_results['failed'],
                'total': stock_results['success'] + stock_results['failed']
            },
            'etfs': {
                'success': etf_results['success'],
                'failed': etf_results['failed'],
                'total': etf_results['success'] + etf_results['failed']
            },
            'total_downloaded': stock_results['success'] + etf_results['success'],
            'total_failed': stock_results['failed'] + etf_results['failed']
        }
        
        # 保存报告
        report_file = os.path.join(self.data_path, 'complete_download_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印报告
        logger.info("\n" + "="*60)
        logger.info("📊 完整数据下载完成报告")
        logger.info("="*60)
        logger.info(f"下载时间: {report['download_time']}")
        logger.info(f"耗时: {report['elapsed_time']}")
        logger.info(f"股票成功: {report['stocks']['success']} / {report['stocks']['total']}")
        logger.info(f"ETF成功: {report['etfs']['success']} / {report['etfs']['total']}")
        logger.info(f"总计成功: {report['total_downloaded']}")
        logger.info(f"总计失败: {report['total_failed']}")
        logger.info("="*60)
        
        # 显示数据目录结构
        self.show_data_structure()
    
    def show_data_structure(self):
        """显示数据目录结构"""
        logger.info("\n📁 数据文件结构:")
        
        for data_type in ['stocks', 'etfs', 'index']:
            dir_path = os.path.join(self.data_path, data_type)
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]
                logger.info(f"  {data_type}/: {len(files)} 个CSV文件")

def main():
    """主函数"""
    try:
        downloader = CompleteDataDownloader()
        downloader.run_download()
    except KeyboardInterrupt:
        logger.info("\n用户中断下载")
    except Exception as e:
        logger.error(f"下载过程出现异常: {e}")

if __name__ == "__main__":
    main()