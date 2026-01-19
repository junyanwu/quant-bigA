#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析项目中的未使用代码和依赖
"""

import ast
import re
from pathlib import Path
from typing import Set, Dict, List

def get_imports_from_file(file_path: Path) -> Set[str]:
    """从文件中提取所有导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            for alias in node.names:
                if module:
                    imports.add(f"{module}.{alias.name}")
                else:
                    imports.add(alias.name)
    
    return imports

def get_used_names_from_file(file_path: Path) -> Set[str]:
    """从文件中提取所有使用的名称"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
    
    return used_names

def analyze_file(file_path: Path) -> Dict[str, List[str]]:
    """分析单个文件"""
    imports = get_imports_from_file(file_path)
    used_names = get_used_names_from_file(file_path)
    
    unused_imports = []
    for imp in imports:
        # 提取导入的名称（去掉模块前缀）
        import_name = imp.split('.')[-1]
        if import_name not in used_names:
            unused_imports.append(imp)
    
    return {
        'file': str(file_path),
        'imports': sorted(list(imports)),
        'unused_imports': sorted(unused_imports)
    }

def main():
    """主函数"""
    project_root = Path('.')
    
    # 分析核心文件
    core_files = [
        'strategies/dca_trading_strategy.py',
        'strategies/indicators.py',
        'backtesting/dca_trading_backtest.py',
        'utils/data_fetcher.py',
        'web/app.py',
        'run_all_etf_backtests.py'
    ]
    
    print('=' * 80)
    print('核心文件分析')
    print('=' * 80)
    
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            result = analyze_file(full_path)
            print(f"\n文件: {file_path}")
            print(f"  导入数: {len(result['imports'])}")
            print(f"  未使用导入数: {len(result['unused_imports'])}")
            
            if result['unused_imports']:
                print(f"  未使用的导入:")
                for imp in result['unused_imports']:
                    print(f"    - {imp}")
    
    # 识别项目中的测试文件
    print('\n' + '=' * 80)
    print('测试文件识别')
    print('=' * 80)
    
    test_files = []
    for file_path in project_root.glob('test_*.py'):
        test_files.append(file_path.name)
    
    for file_path in project_root.glob('*test*.py'):
        if file_path.name not in test_files:
            test_files.append(file_path.name)
    
    if test_files:
        print(f"\n找到 {len(test_files)} 个测试文件:")
        for test_file in sorted(test_files):
            print(f"  - {test_file}")
    else:
        print("\n未找到测试文件")
    
    # 识别重复的回测脚本
    print('\n' + '=' * 80)
    print('重复的回测脚本识别')
    print('=' * 80)
    
    backtest_files = []
    for file_path in project_root.glob('*backtest*.py'):
        backtest_files.append(file_path.name)
    
    for file_path in project_root.glob('run_all*.py'):
        if 'backtest' in file_path.name.lower():
            backtest_files.append(file_path.name)
    
    if backtest_files:
        print(f"\n找到 {len(backtest_files)} 个回测相关文件:")
        for backtest_file in sorted(backtest_files):
            print(f"  - {backtest_file}")
    else:
        print("\n未找到回测文件")

if __name__ == '__main__':
    main()
