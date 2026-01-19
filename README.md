# A股量化交易程序 - 基于VeighNa和QMT

基于VeighNa量化交易框架和QMT交易接口开发的A股量化交易系统，包含数据获取、策略回测和实盘交易功能。

## 项目特性

- 🚀 **基于VeighNa框架**：使用事件驱动架构，支持分布式部署
- 📊 **QMT交易接口**：支持中信建投QMT实盘交易
- 📈 **完整数据获取**：获取A股所有股票和ETF历史数据
- ⚡ **MACD策略**：实现金叉死叉交易策略
- 📋 **专业回测**：完整的回测引擎和评估报告

## 项目结构

```
├── vnpy_apps/           # VeighNa应用模块
│   ├── data_manager.py  # 数据管理应用
│   ├── macd_strategy.py # MACD策略应用
│   └── qmt_gateway.py   # QMT交易接口
├── backtesting/         # 回测引擎
├── config/              # 配置文件
├── data/                # 数据存储
├── strategies/          # 策略模块
├── utils/               # 工具函数
├── webui/               # Web界面
├── main.py              # 主程序入口
└── start_webui.py       # Web UI启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置VeighNa

创建VeighNa配置文件：

```bash
cp config/vnpy_config_template.json config/vnpy_config.json
```

### 3. 获取数据

使用交互式工具下载数据：

```bash
python download_data.py
```

或者使用命令行：

```bash
python main.py --mode download
```

数据会自动缓存到本地，后续使用时会优先读取本地数据，如果数据过期会自动更新。

详细使用说明请查看 [DATA_FETCH_GUIDE.md](DATA_FETCH_GUIDE.md)

### 4. 运行回测

```bash
python main.py --mode backtest --symbol 000001.SH --start 2020-01-01 --end 2024-12-31
```

### 5. 实盘交易

```bash
python main.py --mode live
```

### 6. 启动Web UI

```bash
python start_webui.py
```

## VeighNa架构

项目基于VeighNa的事件驱动架构：

- **主引擎(MainEngine)**：核心引擎，管理所有应用模块
- **事件引擎(EventEngine)**：事件驱动机制
- **应用模块(Apps)**：策略、数据、接口等模块
- **交易接口(Gateways)**：对接不同交易接口

## QMT集成

通过xtquant库集成QMT交易接口，支持：
- 实时行情订阅
- 委托下单撤单
- 账户查询
- 持仓管理

## 策略特性

- **MACD指标**：12/26/9参数配置
- **风险控制**：止损止盈机制
- **仓位管理**：动态仓位调整
- **多周期支持**：日线/分钟线策略