#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据获取模块
支持获取所有股票和ETF的历史K线数据
"""

import pandas as pd
import akshare as ak
import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from config.config import DATA_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AShareDataFetcher:
    """A股数据获取器"""
    
    def __init__(self):
        self.data_path = DATA_CONFIG['data_path']
        self.start_date = DATA_CONFIG['start_date']
        self.end_date = DATA_CONFIG['end_date']
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'stocks'), exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'etfs'), exist_ok=True)
        os.makedirs(os.path.join(self.data_path, 'index'), exist_ok=True)
        
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股所有股票列表"""
        try:
            # 获取A股所有股票列表
            stock_list = ak.stock_info_a_code_name()
            
            # 添加交易所信息
            stock_list['交易所'] = stock_list['code'].apply(
                lambda x: 'SH' if x.startswith(('6', '900', '688')) else 'SZ'
            )
            
            stock_list['symbol'] = stock_list['code'] + '.' + stock_list['交易所']
            
            logger.info(f"获取到 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_etf_list(self) -> pd.DataFrame:
        """获取所有ETF列表"""
        try:
            # 获取ETF列表
            etf_list = ak.fund_etf_spot_em()
            if '代码' in etf_list.columns and '名称' in etf_list.columns:
                etf_list = etf_list[['代码', '名称']].copy()
                etf_list['交易所'] = etf_list['代码'].apply(lambda x: 'SH' if x.startswith('51') else 'SZ')
                etf_list['symbol'] = etf_list['代码'] + '.' + etf_list['交易所']
            else:
                # 备用方法：获取场内基金列表
                etf_list = ak.fund_etf_category_sina(symbol="ETF基金")
                etf_list = etf_list[['代码', '名称']].copy()
                etf_list['交易所'] = etf_list['代码'].apply(lambda x: 'SH' if x.startswith('51') else 'SZ')
                etf_list['symbol'] = etf_list['代码'] + '.' + etf_list['交易所']
            
            logger.info(f"获取到 {len(etf_list)} 只ETF")
            return etf_list
            
        except Exception as e:
            logger.error(f"获取ETF列表失败: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, symbol: str, symbol_type: str = 'stock') -> Optional[pd.DataFrame]:
        """获取单个标的的历史K线数据"""
        try:
            code = symbol.split('.')[0]
            exchange = symbol.split('.')[1]
            
            # 转换日期格式为YYYYMMDD
            start_date_fmt = self.start_date.replace('-', '')
            end_date_fmt = self.end_date.replace('-', '')
            
            if symbol_type == 'stock':
                # 使用统一的A股历史数据接口
                df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                       start_date=start_date_fmt, 
                                       end_date=end_date_fmt, 
                                       adjust="qfq")
            else:  # ETF
                try:
                    # 尝试ETF专用接口
                    df = ak.fund_etf_hist_em(symbol=code, period="daily", 
                                            start_date=start_date_fmt, 
                                            end_date=end_date_fmt, 
                                            adjust="qfq")
                except:
                    # 备用方法：使用普通股票接口
                    df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                           start_date=start_date_fmt, 
                                           end_date=end_date_fmt, 
                                           adjust="qfq")
            
            if df.empty:
                return None
            
            # 标准化列名 - 根据实际返回的列数动态处理
            expected_columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                               'change_percent', 'change_amount', 'turnover']
            
            # 如果列数不匹配，动态调整列名
            if len(df.columns) == 12:
                df.columns = ['date', 'symbol', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                             'change_percent', 'change_amount', 'turnover']
            elif len(df.columns) == 11:
                df.columns = expected_columns
            else:
                # 其他情况，使用原始列名
                logger.warning(f"{symbol} 返回的列数异常: {len(df.columns)}，使用原始列名")
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            return df
            
        except Exception as e:
            logger.warning(f"获取 {symbol} 数据失败: {e}")
            return None
    
    def download_all_data(self, max_workers: int = 10) -> Dict[str, List[str]]:
        """批量下载所有数据"""
        import concurrent.futures
        
        results = {'stocks': [], 'etfs': [], 'failed': []}
        
        # 获取股票和ETF列表
        stock_list = self.get_stock_list()
        etf_list = self.get_etf_list()
        
        all_symbols = []
        
        # 添加股票
        for _, row in stock_list.iterrows():
            # 检查列名，适应不同的列名格式
            name_col = '名称' if '名称' in stock_list.columns else 'name' if 'name' in stock_list.columns else '代码'
            all_symbols.append(('stock', row['symbol'], row.get(name_col, row['symbol'])))
        
        # 添加ETF
        for _, row in etf_list.iterrows():
            # 检查列名，适应不同的列名格式
            name_col = '名称' if '名称' in etf_list.columns else 'name' if 'name' in etf_list.columns else '代码'
            all_symbols.append(('etf', row['symbol'], row.get(name_col, row['symbol'])))
        
        logger.info(f"开始下载 {len(all_symbols)} 个标的的数据...")
        
        def download_symbol(symbol_info):
            symbol_type, symbol, name = symbol_info
            
            try:
                data = self.get_historical_data(symbol, symbol_type)
                if data is not None and not data.empty:
                    # 保存数据
                    if symbol_type == 'stock':
                        file_path = os.path.join(self.data_path, 'stocks', f"{symbol}.csv")
                    else:
                        file_path = os.path.join(self.data_path, 'etfs', f"{symbol}.csv")
                    
                    data.to_csv(file_path)
                    
                    # 添加指数数据到结果
                    if symbol_type == 'stock':
                        results['stocks'].append(symbol)
                    else:
                        results['etfs'].append(symbol)
                    
                    logger.info(f"成功下载 {symbol} ({name}) 数据，共 {len(data)} 条记录")
                    return True
                else:
                    results['failed'].append(symbol)
                    return False
                    
            except Exception as e:
                logger.error(f"下载 {symbol} 数据失败: {e}")
                results['failed'].append(symbol)
                return False
        
        # 使用线程池并行下载
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_symbol, symbol_info) for symbol_info in all_symbols]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                future.result()
        
        # 下载指数数据
        self.download_index_data()
        
        logger.info(f"数据下载完成！成功: {len(results['stocks'])} 只股票, {len(results['etfs'])} 只ETF, 失败: {len(results['failed'])}")
        
        # 保存下载结果
        with open(os.path.join(self.data_path, 'download_summary.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results
    
    def download_index_data(self):
        """下载主要指数数据"""
        index_symbols = ['000001.SH', '000300.SH', '000905.SH', '399001.SZ', '399006.SZ']
        
        # 转换日期格式为YYYYMMDD
        start_date_fmt = self.start_date.replace('-', '')
        end_date_fmt = self.end_date.replace('-', '')
        
        for symbol in index_symbols:
            try:
                code = symbol.split('.')[0]
                # 使用新的指数接口
                df = ak.index_zh_a_hist(symbol=code, period="daily", 
                                       start_date=start_date_fmt, 
                                       end_date=end_date_fmt)
                
                if not df.empty:
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
                    df['date'] = pd.to_datetime(df['date'])
                    df['symbol'] = symbol
                    df = df.set_index('date').sort_index()
                    
                    file_path = os.path.join(self.data_path, 'index', f"{symbol}.csv")
                    df.to_csv(file_path)
                    logger.info(f"成功下载指数 {symbol} 数据")
                
            except Exception as e:
                logger.error(f"下载指数 {symbol} 数据失败: {e}")
    
    def load_data(self, symbol: str, symbol_type: str = 'stock') -> Optional[pd.DataFrame]:
        """从本地文件加载数据"""
        try:
            if symbol_type == 'stock':
                file_path = os.path.join(self.data_path, 'stocks', f"{symbol}.csv")
            elif symbol_type == 'etf':
                file_path = os.path.join(self.data_path, 'etfs', f"{symbol}.csv")
            else:
                file_path = os.path.join(self.data_path, 'index', f"{symbol}.csv")
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, index_col='date', parse_dates=True)
                return df
            else:
                return None
                
        except Exception as e:
            logger.error(f"加载 {symbol} 数据失败: {e}")
            return None
    
    def get_data(self, symbol: str, symbol_type: str = 'stock', 
                 start_date: Optional[str] = None, end_date: Optional[str] = None,
                 force_update: bool = False) -> Optional[pd.DataFrame]:
        """
        智能获取数据：优先使用本地数据，如果缺失或过期则从网上下载更新
        
        Args:
            symbol: 标的代码，如 '000001.SH'
            symbol_type: 标的类型 ('stock', 'etf', 'index')
            start_date: 开始日期，如 '2020-01-01'，默认使用配置中的开始日期
            end_date: 结束日期，如 '2024-12-31'，默认使用配置中的结束日期
            force_update: 是否强制从网上重新下载
            
        Returns:
            包含历史数据的DataFrame，如果失败则返回None
        """
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date
        
        # 尝试从本地加载数据
        local_data = None
        if not force_update:
            local_data = self.load_data(symbol, symbol_type)
        
        # 判断是否需要更新
        need_update = force_update or (local_data is None)
        last_date = None
        
        if local_data is not None and not local_data.empty:
            last_date = local_data.index[-1]
            # 检查数据是否过期（最后日期早于结束日期）
            if last_date < pd.to_datetime(end_date):
                need_update = True
                logger.info(f"{symbol} 本地数据最后日期: {last_date.date()}, 需要更新")
            else:
                logger.info(f"{symbol} 使用本地数据，日期范围: {local_data.index[0].date()} - {local_data.index[-1].date()}")
        
        # 如果需要更新或本地没有数据
        if need_update:
            logger.info(f"正在从网上下载 {symbol} 的数据...")
            
            # 如果本地有数据，只下载增量数据
            if local_data is not None and not local_data.empty:
                # 从最后日期的下一天开始下载
                new_start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                
                # 临时修改开始日期
                original_start = self.start_date
                self.start_date = new_start_date
                
                try:
                    new_data = self.get_historical_data(symbol, symbol_type)
                    
                    # 恢复原始开始日期
                    self.start_date = original_start
                    
                    if new_data is not None and not new_data.empty:
                        # 合并数据
                        combined_data = pd.concat([local_data, new_data])
                        # 去除重复数据
                        combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                        combined_data = combined_data.sort_index()
                        
                        # 保存合并后的数据
                        if symbol_type == 'stock':
                            file_path = os.path.join(self.data_path, 'stocks', f"{symbol}.csv")
                        elif symbol_type == 'etf':
                            file_path = os.path.join(self.data_path, 'etfs', f"{symbol}.csv")
                        else:
                            file_path = os.path.join(self.data_path, 'index', f"{symbol}.csv")
                        
                        combined_data.to_csv(file_path)
                        logger.info(f"{symbol} 数据更新成功，新增 {len(new_data)} 条记录")
                        
                        # 筛选日期范围
                        combined_data = combined_data.loc[start_date:end_date]
                        return combined_data
                    else:
                        logger.debug(f"{symbol} 增量数据暂不可用，使用本地数据")
                        return local_data.loc[start_date:end_date]
                        
                except Exception as e:
                    logger.debug(f"{symbol} 增量数据暂不可用: {e}")
                    self.start_date = original_start
                    return local_data.loc[start_date:end_date] if local_data is not None else None
            else:
                # 本地没有数据，下载全部数据
                try:
                    # 临时修改开始和结束日期
                    original_start = self.start_date
                    original_end = self.end_date
                    self.start_date = start_date
                    self.end_date = end_date
                    
                    data = self.get_historical_data(symbol, symbol_type)
                    
                    # 恢复原始日期
                    self.start_date = original_start
                    self.end_date = original_end
                    
                    if data is not None and not data.empty:
                        # 保存数据
                        if symbol_type == 'stock':
                            file_path = os.path.join(self.data_path, 'stocks', f"{symbol}.csv")
                        elif symbol_type == 'etf':
                            file_path = os.path.join(self.data_path, 'etfs', f"{symbol}.csv")
                        else:
                            file_path = os.path.join(self.data_path, 'index', f"{symbol}.csv")
                        
                        data.to_csv(file_path)
                        logger.info(f"{symbol} 数据下载成功，共 {len(data)} 条记录")
                        
                        # 筛选日期范围
                        data = data.loc[start_date:end_date]
                        return data
                    else:
                        logger.error(f"{symbol} 数据下载失败")
                        return None
                except Exception as e:
                    logger.error(f"{symbol} 数据下载失败: {e}")
                    # 恢复原始日期
                    self.start_date = original_start
                    self.end_date = original_end
                    return None
        else:
            # 直接使用本地数据
            return local_data.loc[start_date:end_date]
    
    def get_available_symbols(self) -> Dict[str, List[str]]:
        """获取本地可用的标的列表"""
        available = {'stocks': [], 'etfs': [], 'index': []}
        
        # 检查股票数据
        stock_files = os.listdir(os.path.join(self.data_path, 'stocks'))
        available['stocks'] = [f.replace('.csv', '') for f in stock_files if f.endswith('.csv')]
        
        # 检查ETF数据
        etf_files = os.listdir(os.path.join(self.data_path, 'etfs'))
        available['etfs'] = [f.replace('.csv', '') for f in etf_files if f.endswith('.csv')]
        
        # 检查指数数据
        index_files = os.listdir(os.path.join(self.data_path, 'index'))
        available['index'] = [f.replace('.csv', '') for f in index_files if f.endswith('.csv')]
        
        return available


def main():
    """主函数 - 用于测试数据获取"""
    fetcher = AShareDataFetcher()
    
    # 下载所有数据
    results = fetcher.download_all_data(max_workers=5)
    
    # 显示下载结果
    print("\n=== 数据下载结果 ===")
    print(f"成功下载股票: {len(results['stocks'])} 只")
    print(f"成功下载ETF: {len(results['etfs'])} 只")
    print(f"失败: {len(results['failed'])} 个")
    
    # 显示可用的标的
    available = fetcher.get_available_symbols()
    print(f"\n=== 本地可用数据 ===")
    print(f"股票: {len(available['stocks'])} 只")
    print(f"ETF: {len(available['etfs'])} 只")
    print(f"指数: {len(available['index'])} 个")


if __name__ == "__main__":
    main()