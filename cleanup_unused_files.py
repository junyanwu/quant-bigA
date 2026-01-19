#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理未使用的文件
"""

import os
from pathlib import Path

def main():
    """主函数"""
    project_root = Path('.')
    
    # 需要删除的测试文件（保留test_api.py和analyze_results.py）
    test_files_to_delete = [
        'test_akshare_920522.py',
        'test_920522_data.py',
        'test_fixed_backtest.py',
        'check_data_years.py',
        'test_incremental_download.py',
        'check_summary_consistency.py',
        'test_multiple_backtests.py',
        'test_589960_save.py',
        'test_589960_backtest2.py',
        'test_589960_backtest.py',
        'test_date_filter.py',
        'check_589960_data.py',
        'get_special_stocks.py',
        'get_stock_names.py',
        'update_summary_names.py',
        'test_akshare_api.py',
        'check_missing_names.py',
        'regenerate_summary.py',
        'test_backtest.py',
        'print_backtest_results.py',
        'generate_final_report.py',
        'retry_failed_downloads.py',
        'example_data_fetch.py',
        'download_data.py',
        'fix_problematic_symbols.py',
        'find_problematic_symbols.py'
    ]
    
    # 需要删除的重复回测脚本
    backtest_files_to_delete = [
        'run_all_backtests.py',
        'run_all_local_backtests.py',
        'run_all_local_backtests_multiprocess.py'
    ]
    
    # 需要删除的vnpy相关文件（未使用）
    vnpy_files_to_delete = [
        'vnpy_apps/qmt_gateway.py',
        'vnpy_apps/data_manager.py',
        'vnpy_apps/macd_strategy.py',
        'vnpy_apps/__init__.py',
        'vnpy_apps'
    ]
    
    # 需要删除的webui相关文件（使用web替代）
    webui_files_to_delete = [
        'webui/app.py',
        'webui/run_webui.py',
        'webui'
    ]
    
    # 需要删除的其他文件
    other_files_to_delete = [
        'start_webui.py',
        'main.py',
        'check_data_years.py',
        'check_summary_consistency.py',
        'check_missing_names.py',
        'check_589960_data.py',
        'get_special_stocks.py',
        'get_stock_names.py',
        'update_summary_names.py',
        'regenerate_summary.py',
        'print_backtest_results.py',
        'generate_final_report.py',
        'retry_failed_downloads.py',
        'example_data_fetch.py',
        'download_data.py',
        'fix_problematic_symbols.py',
        'find_problematic_symbols.py'
    ]
    
    # 合并所有需要删除的文件
    all_files_to_delete = test_files_to_delete + backtest_files_to_delete + vnpy_files_to_delete + webui_files_to_delete + other_files_to_delete
    
    print('=' * 80)
    print('准备删除以下文件:')
    print('=' * 80)
    
    deleted_count = 0
    for file_name in all_files_to_delete:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  - {file_name}")
            deleted_count += 1
        else:
            print(f"  - {file_name} (不存在)")
    
    print(f'\n总计: {deleted_count} 个文件')
    
    # 确认删除
    print('\n' + '=' * 80)
    confirm = input('确认删除这些文件吗？(yes/no): ')
    
    if confirm.lower() in ['yes', 'y']:
        for file_name in all_files_to_delete:
            file_path = project_root / file_name
            if file_path.exists():
                if file_path.is_file():
                    os.remove(file_path)
                    print(f"✅ 已删除: {file_name}")
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
                    print(f"✅ 已删除目录: {file_name}")
        
        print('\n' + '=' * 80)
        print('清理完成！')
    else:
        print('\n已取消删除操作')

if __name__ == '__main__':
    main()
