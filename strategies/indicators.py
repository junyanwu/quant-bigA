#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算模块
计算MACD、成交量、ATR、估值等指标
"""

import pandas as pd

def calculate_macd(df: pd.DataFrame, fast: int = 6, slow: int = 13, signal: int = 5, 
                  window: int = 20) -> pd.DataFrame:
    """
    计算MACD指标及其上下轨
    
    第三轮优化后的参数：
    - fast: 从12改为6，更敏感
    - slow: 从26改为13，更敏感
    - signal: 从9改为5，更敏感
    
    Args:
        df: 包含OHLCV数据的DataFrame
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
        window: 上下轨计算窗口
        
    Returns:
        添加了MACD相关列的DataFrame
    """
    df = df.copy()
    
    # 计算EMA
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # 计算MACD线
    df['macd'] = ema_fast - ema_slow
    
    # 计算信号线
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    # 计算柱状图
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 计算MACD上下轨（使用滚动分位数）
    df['macd_upper'] = df['macd'].rolling(window=window).quantile(0.8)
    df['macd_lower'] = df['macd'].rolling(window=window).quantile(0.2)
    
    return df


def calculate_volume_indicators(df: pd.DataFrame, volume_ma_window: int = 20) -> pd.DataFrame:
    """
    计算成交量相关指标
    
    Args:
        df: 包含OHLCV数据的DataFrame
        volume_ma_window: 成交量均线周期
        
    Returns:
        添加了成交量指标的DataFrame
    """
    df = df.copy()
    
    # 计算成交量均线
    df['volume_ma'] = df['volume'].rolling(window=volume_ma_window).mean()
    
    # 计算成交量比率
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    # 判断是否放量（成交量超过均值的1.5倍）
    df['is_volume_surge'] = df['volume_ratio'] > 1.5
    
    # 判断是否缩量（成交量低于均值的0.8倍）
    df['is_volume_shrink'] = df['volume_ratio'] < 0.8
    
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算ATR（平均真实波幅）
    
    Args:
        df: 包含OHLC数据的DataFrame
        period: ATR周期
        
    Returns:
        添加了ATR列的DataFrame
    """
    df = df.copy()
    
    # 计算真实波幅
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # 计算ATR
    df['atr'] = df['tr'].rolling(window=period).mean()
    
    # 计算ATR比率（相对于价格）
    df['atr_ratio'] = df['atr'] / df['close']
    
    return df


def check_chip_consolidation(df: pd.DataFrame, atr_window: int = 20, 
                          volume_window: int = 20, atr_threshold: float = 0.02) -> pd.Series:
    """
    检查筹码结构是否整理完毕
    
    条件：
    1. ATR比率低于阈值（波动收敛）
    2. 成交量萎缩
    
    Args:
        df: 包含技术指标的DataFrame
        atr_window: ATR计算窗口
        volume_window: 成交量窗口
        atr_threshold: ATR比率阈值
        
    Returns:
        布尔Series，True表示筹码整理完毕
    """
    df = df.copy()
    
    # 波动收敛
    is_atr_low = df['atr_ratio'] < atr_threshold
    
    # 成交量萎缩
    is_volume_shrink = df['is_volume_shrink']
    
    # 筹码整理完毕
    df['chip_consolidated'] = is_atr_low & is_volume_shrink
    
    return df['chip_consolidated']


def calculate_valuation_metrics(df: pd.DataFrame, pe_window: int = 252) -> pd.DataFrame:
    """
    计算估值指标（使用PE百分位）
    
    注意：这里使用价格作为估值的代理，实际应用中应该使用真实的PE/PB数据
    
    Args:
        df: 包含价格数据的DataFrame
        pe_window: 估值窗口（默认252个交易日，约1年）
        
    Returns:
        添加了估值指标的DataFrame
    """
    df = df.copy()
    
    # 使用价格作为估值代理（实际应该使用PE/PB）
    # 计算价格百分位
    df['price_percentile'] = df['close'].rolling(window=pe_window).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    )
    
    # 判断是否高估（超过80%分位数）
    df['is_overvalued'] = df['price_percentile'] > 0.8
    
    # 判断是否低估（低于20%分位数）
    df['is_undervalued'] = df['price_percentile'] < 0.2
    
    return df


def calculate_all_indicators(df: pd.DataFrame,
                          volume_window: int = 20,
                          atr_period: int = 14,
                          valuation_window: int = 252,
                          ma_short: int = 20,
                          ma_long: int = 60) -> pd.DataFrame:
    """
    计算所有技术指标
    
    第九轮优化：添加阳线判断、大盘指标
    第十一轮优化：添加MA5均线
    
    Args:
        df: 包含OHLCV数据的DataFrame
        volume_window: 成交量窗口
        atr_period: ATR周期
        valuation_window: 估值窗口
        ma_short: 短期移动平均线周期
        ma_long: 长期移动平均线周期
        
    Returns:
        包含所有技术指标的DataFrame
    """
    # 计算MACD
    df = calculate_macd(df)
    
    # 计算成交量指标
    df = calculate_volume_indicators(df, volume_window)
    
    # 计算ATR
    df = calculate_atr(df, atr_period)
    
    # 计算筹码整理指标
    df['chip_consolidated'] = check_chip_consolidation(df)
    
    # 计算估值指标
    df = calculate_valuation_metrics(df, valuation_window)
    
    # 计算移动平均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma_short'] = df['close'].rolling(window=ma_short).mean()
    df['ma_long'] = df['close'].rolling(window=ma_long).mean()
    
    # 判断趋势
    df['is_uptrend'] = df['ma_short'] > df['ma_long']
    df['is_downtrend'] = df['ma_short'] < df['ma_long']
    
    # 判断是否是阳线（收盘价高于开盘价）
    df['is_yang'] = df['close'] > df['open']
    
    # 保存MACD柱状图的历史值
    df['macd_hist_prev'] = df['macd_hist'].shift(1)
    df['macd_hist_prev2'] = df['macd_hist'].shift(2)
    
    return df


def calculate_index_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算大盘指标
    
    第九轮优化：添加大盘下跌和反弹指标
    
    Args:
        df: 包含OHLCV数据的DataFrame（大盘数据）
        
    Returns:
        添加了大盘指标的DataFrame
    """
    df = df.copy()
    
    # 计算日收益率
    df['daily_return'] = df['close'].pct_change()
    
    # 计算累计收益率（用于判断反弹）
    df['cum_return'] = df['daily_return'].cumsum()
    
    # 判断大盘下跌超过2%
    df['drop_2'] = df['daily_return'] < -0.02
    
    # 判断大盘下跌超过1%但小于2%
    df['drop_1'] = (df['daily_return'] < -0.01) & (df['daily_return'] >= -0.02)
    
    # 计算反弹幅度
    df['rebound'] = df['daily_return'] - df['daily_return'].shift(1)
    
    # 判断大盘下跌超过2%后反弹0.3%
    df['drop_2_rebound_03'] = df['drop_2'].shift(1) & (df['daily_return'] > 0.003)
    
    # 判断大盘下跌超过1%但小于2%后反弹0.2%
    df['drop_1_rebound_02'] = df['drop_1'].shift(1) & (df['daily_return'] > 0.002)
    
    return df


def get_trading_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成交易信号
    
    第三轮优化后的信号逻辑：
    
    加仓信号（满足任意一个）：
    1. 下跌放量（成交量超过1.5倍）
    2. MACD下轨
    3. 筹码结构整理完毕（ATR比率低于2%且成交量萎缩）
    4. MACD金叉（MACD上穿信号线）
    5. 新增：MACD柱状图由负转正
    
    减仓信号（满足任意一个）：
    1. MACD上轨且放量下跌
    2. MACD死叉（MACD下穿信号线）
    3. 新增：MACD柱状图由正转负
    
    优化：
    - 增加MACD柱状图变化信号，更及时捕捉趋势变化
    - 提高信号质量，减少假信号
    """
    df = df.copy()
    
    # 加仓信号
    # 1. 下跌放量
    df['signal_add_1'] = (df['close'] < df['close'].shift(1)) & df['is_volume_surge']
    
    # 2. MACD下轨
    df['signal_add_2'] = df['macd'] < df['macd_lower']
    
    # 3. 筹码结构整理完毕
    df['signal_add_3'] = df['chip_consolidated']
    
    # 4. MACD金叉
    df['macd_cross_up'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df['signal_add_4'] = df['macd_cross_up']
    
    # 5. MACD柱状图由负转正（新增）
    df['macd_hist_cross_up'] = (df['macd_hist'] > 0) & (df['macd_hist'].shift(1) <= 0)
    df['signal_add_5'] = df['macd_hist_cross_up']
    
    # 综合加仓信号（满足任意一个条件）
    df['signal_add'] = df['signal_add_1'] | df['signal_add_2'] | df['signal_add_3'] | df['signal_add_4'] | df['signal_add_5']
    
    # 减仓信号
    # 1. MACD上轨且放量下跌
    df['signal_reduce_1'] = (df['macd'] > df['macd_upper']) & \
                           (df['close'] < df['close'].shift(1)) & \
                           df['is_volume_surge']
    
    # 2. MACD死叉
    df['macd_cross_down'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
    df['signal_reduce_2'] = df['macd_cross_down']
    
    # 3. MACD柱状图由正转负（新增）
    df['macd_hist_cross_down'] = (df['macd_hist'] < 0) & (df['macd_hist'].shift(1) >= 0)
    df['signal_reduce_3'] = df['macd_hist_cross_down']
    
    # 综合减仓信号
    df['signal_reduce'] = df['signal_reduce_1'] | df['signal_reduce_2'] | df['signal_reduce_3']
    
    return df


if __name__ == "__main__":
    # 测试代码
    from utils.data_fetcher import AShareDataFetcher
    
    fetcher = AShareDataFetcher()
    df = fetcher.get_data('510300.SH', 'etf', '2023-01-01', '2024-12-31')
    
    if df is not None:
        df = calculate_all_indicators(df)
        df = get_trading_signals(df)
        
        print("技术指标计算完成")
        print(f"数据行数: {len(df)}")
        print(f"列名: {df.columns.tolist()}")
        print(f"\n最后5行数据:")
        print(df.tail())