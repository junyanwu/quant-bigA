# A股数据下载和缓存使用指南

## 功能概述

本项目实现了智能的A股数据下载和缓存机制，具有以下特点：

1. **自动缓存**：首次下载的数据会保存在本地，后续使用时优先从本地读取
2. **智能更新**：如果本地数据过期，会自动下载增量数据并合并
3. **多类型支持**：支持股票、ETF、指数等多种标的类型
4. **批量下载**：支持批量下载所有A股和ETF数据

## 快速开始

### 1. 下载所有数据

使用交互式工具下载所有A股和ETF数据：

```bash
python download_data.py
```

选择"1. 下载所有股票和ETF数据"，程序会自动下载所有数据到本地。

### 2. 在代码中使用智能数据获取

```python
from utils.data_fetcher import AShareDataFetcher

# 创建数据获取器
fetcher = AShareDataFetcher()

# 获取数据（自动处理缓存和更新）
data = fetcher.get_data('000001.SZ', 'stock', 
                        start_date='2024-01-01', 
                        end_date='2024-12-31')

# 查看数据
print(data.head())
```

## 详细使用说明

### 基本用法

#### 获取单个标的数据

```python
from utils.data_fetcher import AShareDataFetcher

fetcher = AShareDataFetcher()

# 获取股票数据
data = fetcher.get_data('000001.SZ', 'stock', 
                        start_date='2024-01-01', 
                        end_date='2024-12-31')

# 获取ETF数据
data = fetcher.get_data('510300.SH', 'etf', 
                        start_date='2024-01-01', 
                        end_date='2024-12-31')

# 获取指数数据
data = fetcher.get_data('000001.SH', 'index', 
                        start_date='2024-01-01', 
                        end_date='2024-12-31')
```

#### 查看本地数据

```python
fetcher = AShareDataFetcher()

# 获取本地可用的标的列表
available = fetcher.get_available_symbols()

print(f"股票: {len(available['stocks'])} 只")
print(f"ETF: {len(available['etfs'])} 只")
print(f"指数: {len(available['index'])} 个")
```

### 高级用法

#### 强制更新数据

```python
# 强制从网上重新下载，不使用缓存
data = fetcher.get_data('000001.SZ', 'stock', 
                        start_date='2024-01-01', 
                        end_date='2024-12-31',
                        force_update=True)
```

#### 使用默认日期范围

```python
# 不指定日期范围，使用配置文件中的默认范围
data = fetcher.get_data('000001.SZ', 'stock')
```

#### 在回测中使用

```python
from utils.data_fetcher import AShareDataFetcher

def run_backtest(symbol, start_date, end_date):
    fetcher = AShareDataFetcher()
    
    # 获取回测数据
    data = fetcher.get_data(symbol, 'stock', 
                           start_date=start_date, 
                           end_date=end_date)
    
    if data is not None and not data.empty:
        # 执行回测逻辑
        print(f"获取到 {len(data)} 条数据")
        print(f"数据范围: {data.index[0]} - {data.index[-1]}")
        
        # 你的回测代码...
    else:
        print("获取数据失败")
```

## 数据存储结构

下载的数据会保存在 `./data` 目录下：

```
data/
├── stocks/          # 股票数据
│   ├── 000001.SZ.csv
│   ├── 000002.SZ.csv
│   └── ...
├── etfs/            # ETF数据
│   ├── 510300.SH.csv
│   └── ...
├── index/           # 指数数据
│   ├── 000001.SH.csv
│   └── ...
└── download_summary.json  # 下载摘要
```

## 数据格式

每个CSV文件包含以下列：

- `date`: 日期（索引）
- `symbol`: 标的代码
- `open`: 开盘价
- `close`: 收盘价
- `high`: 最高价
- `low`: 最低价
- `volume`: 成交量
- `amount`: 成交额
- `amplitude`: 振幅
- `change_percent`: 涨跌幅
- `change_amount`: 涨跌额
- `turnover`: 换手率

## 交互式工具

运行 `download_data.py` 可以使用交互式工具：

```bash
python download_data.py
```

菜单选项：

1. **下载所有股票和ETF数据**：批量下载所有数据
2. **下载单个标的数据**：下载指定标的的数据
3. **更新现有数据**：更新本地已有的数据
4. **查看本地数据**：查看本地已有的数据统计
0. **退出**：退出程序

## 配置

在 `config/config.py` 中可以配置数据参数：

```python
DATA_CONFIG = {
    'data_path': './data',              # 数据存储路径
    'start_date': '2015-01-01',         # 默认开始日期
    'end_date': datetime.now().strftime('%Y-%m-%d'),  # 默认结束日期
    'max_workers': 10,                  # 并行下载线程数
    'retry_times': 3,                   # 重试次数
    'batch_size': 100                   # 批量下载大小
}
```

## 使用示例

查看完整的使用示例：

```bash
python example_data_fetch.py
```

示例包括：

1. 基本使用 - 获取单个标的数据
2. 缓存使用 - 第二次获取同一数据会使用本地缓存
3. 强制更新 - 强制从网上重新下载数据
4. 查看本地数据 - 查看本地已有的数据统计
5. 回测中使用 - 模拟回测时获取数据

## 注意事项

1. **首次下载较慢**：第一次下载所有数据可能需要较长时间，请耐心等待
2. **网络要求**：需要稳定的网络连接以从akshare获取数据
3. **磁盘空间**：所有A股和ETF数据大约需要几GB的磁盘空间
4. **数据更新**：建议定期运行更新功能以保持数据最新

## 常见问题

### Q: 为什么第一次获取数据很慢？

A: 第一次获取数据需要从网上下载，后续使用会从本地读取，速度会快很多。

### Q: 如何更新本地数据？

A: 使用 `download_data.py` 选择"3. 更新现有数据"，或在代码中使用 `force_update=True` 参数。

### Q: 数据存储在哪里？

A: 数据存储在 `./data` 目录下，按类型分为 `stocks/`、`etfs/` 和 `index/` 子目录。

### Q: 如何在回测中使用？

A: 直接调用 `fetcher.get_data()` 方法，它会自动处理缓存和更新，无需手动管理数据文件。

## 技术支持

如有问题，请查看：
- 项目README.md
- DATA_DOWNLOAD_GUIDE.md
- 或提交Issue
