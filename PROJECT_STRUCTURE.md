# quant-bigA 项目目录结构说明

## 项目概述

quant-bigA 是一个基于Python的量化交易策略回测系统，主要功能包括：
- 定投+做T策略实现
- 技术指标计算
- 回测引擎
- Web可视化界面
- 数据获取和管理

## 目录结构

```
quant-bigA/
├── config/                    # 配置文件目录
│   └── config.py          # 全局配置参数
│
├── strategies/                # 策略实现目录
│   ├── __init__.py        # 策略模块初始化
│   ├── dca_trading_strategy.py  # 定投+做T策略实现
│   ├── dca_strategy.py    # 旧版定投策略（待删除）
│   └── indicators.py      # 技术指标计算
│
├── backtesting/              # 回测引擎目录
│   ├── __init__.py        # 回测模块初始化
│   ├── dca_trading_backtest.py  # 定投+做T回测引擎
│   ├── dca_backtest_engine.py  # 旧版回测引擎（待删除）
│   └── backtest_engine.py  # 通用回测引擎（待整合）
│
├── utils/                    # 工具函数目录
│   └── data_fetcher.py   # 数据获取和缓存
│
├── web/                      # Web应用目录
│   ├── README.md           # Web应用说明
│   ├── app.py              # Flask Web应用
│   └── templates/          # HTML模板
│
├── data/                     # 数据文件目录
│   ├── etfs/               # ETF数据
│   ├── stocks/             # 股票数据
│   ├── indexes/             # 指数数据
│   └── symbol_names.json   # 标的名称映射
│
├── results/                  # 回测结果目录
│   └── all_backtest_summary.csv  # 所有标的回测汇总
│
├── scripts/                  # 脚本文件目录
│   └── run_all_etf_backtests.py  # 批量回测脚本
│
├── tests/                    # 测试文件目录（待创建）
│   ├── __init__.py        # 测试模块初始化
│   ├── test_strategy.py    # 策略测试
│   ├── test_backtest.py    # 回测测试
│   └── test_indicators.py  # 指标测试
│
├── docs/                     # 文档目录（待创建）
│   ├── API.md              # API文档
│   ├── STRATEGY.md          # 策略文档
│   └── DEPLOYMENT.md        # 部署文档
│
├── README.md                 # 项目主说明文档
├── .gitignore               # Git忽略文件配置
├── requirements.txt           # Python依赖包列表（待创建）
└── setup.py                 # 项目安装脚本（待创建）
```

## 目录职责说明

### config/
**职责**：存储全局配置参数
**包含文件**：
- `config.py`：全局配置，如API密钥、默认参数等

### strategies/
**职责**：实现交易策略和计算技术指标
**包含文件**：
- `dca_trading_strategy.py`：定投+做T策略的主要实现
- `indicators.py`：技术指标计算（MACD、ATR、MA等）
- `dca_strategy.py`：旧版定投策略（待删除）

### backtesting/
**职责**：实现回测引擎
**包含文件**：
- `dca_trading_backtest.py`：定投+做T策略的回测引擎
- `dca_backtest_engine.py`：旧版回测引擎（待删除）
- `backtest_engine.py`：通用回测引擎（待整合）

### utils/
**职责**：提供工具函数和辅助功能
**包含文件**：
- `data_fetcher.py`：数据获取、缓存和管理

### web/
**职责**：提供Web可视化界面
**包含文件**：
- `app.py`：Flask Web应用主文件
- `templates/`：HTML模板文件
- `README.md`：Web应用说明

### data/
**职责**：存储历史价格数据
**包含目录**：
- `etfs/`：ETF历史数据（CSV格式）
- `stocks/`：股票历史数据（CSV格式）
- `indexes/`：指数历史数据（CSV格式）
- `symbol_names.json`：标的代码到名称的映射

### results/
**职责**：存储回测结果
**包含文件**：
- `all_backtest_summary.csv`：所有标的的回测汇总结果

### scripts/
**职责**：存储可执行的脚本
**包含文件**：
- `run_all_etf_backtests.py`：批量回测所有ETF的脚本

### tests/
**职责**：存储单元测试和集成测试
**包含文件**（待创建）：
- `test_strategy.py`：策略单元测试
- `test_backtest.py`：回测引擎测试
- `test_indicators.py`：指标计算测试

### docs/
**职责**：存储项目文档
**包含文件**（待创建）：
- `API.md`：API接口文档
- `STRATEGY.md`：策略说明文档
- `DEPLOYMENT.md`：部署指南

## 文件组织规则

### 1. 模块化原则
- 每个目录代表一个功能模块
- 模块之间通过明确的接口进行交互
- 避免循环依赖

### 2. 命名规范
- 文件名使用小写字母和下划线：`dca_trading_strategy.py`
- 类名使用大驼峰：`DcaTradingStrategy`
- 函数名使用小写和下划线：`calculate_shares`
- 常量使用大写和下划线：`MAX_LOSS_RATIO`

### 3. 导入规范
- 相对导入优先：`from strategies.indicators import calculate_all_indicators`
- 绝对导入用于第三方库：`import pandas as pd`
- 避免通配符导入：`from module import *`

### 4. 代码注释规范
- 模块级文档字符串：描述模块功能
- 类级文档字符串：描述类功能
- 函数级文档字符串：描述函数参数和返回值
- 行内注释：解释复杂逻辑

### 5. 测试规范
- 测试文件命名：`test_<module>.py`
- 测试函数命名：`test_<function>`
- 测试覆盖率要求：> 80%

### 6. Git提交规范
- 提交信息格式：`<type>(<scope>): <subject>`
- 类型：`feat`/`fix`/`refactor`/`docs`/`test`/`chore`
- 示例：`feat(strategy): add ATR-based stop loss`

## 待优化项

1. **删除旧版文件**：
   - `strategies/dca_strategy.py`
   - `backtesting/dca_backtest_engine.py`
   - `backtesting/backtest_engine.py`

2. **创建测试目录**：
   - `tests/` 目录
   - 单元测试文件

3. **创建文档目录**：
   - `docs/` 目录
   - API文档
   - 策略文档

4. **创建依赖文件**：
   - `requirements.txt`
   - `setup.py`

5. **整理脚本文件**：
   - 将临时脚本移到 `scripts/` 目录
   - 删除临时分析脚本

## 代码质量要求

1. **代码复杂度**：函数圈复杂度 < 10
2. **代码重复率**：< 5%
3. **测试覆盖率**：> 80%
4. **文档覆盖率**：> 90%
5. **类型注解**：所有公共函数和类方法
