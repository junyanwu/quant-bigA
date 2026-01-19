#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网页端API返回的数据
"""

import requests
import json

# 测试API端点
api_url = 'http://localhost:5001/api/summary'

try:
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        print('API返回数据统计:')
        print(f'总标的数: {len(data)}')
        
        if len(data) > 0:
            # 检查第一个标的的生成时间
            first_item = data[0]
            print(f'第一个标的: {first_item.get("symbol", "N/A")}')
            print(f'总收益率: {first_item.get("total_return", 0)*100:.2f}%')
            print(f'年化收益率: {first_item.get("annual_return", 0)*100:.2f}%')
            
            # 检查是否有generated_at字段
            if 'generated_at' in first_item:
                print(f'生成时间: {first_item["generated_at"]}')
            else:
                print('⚠️  没有找到generated_at字段')
            
            # 统计平均收益率
            avg_return = sum(item.get('total_return', 0) for item in data) / len(data)
            avg_annual_return = sum(item.get('annual_return', 0) for item in data) / len(data)
            
            print(f'\n平均总收益率: {avg_return*100:.2f}%')
            print(f'平均年化收益率: {avg_annual_return*100:.2f}%')
            
            # 判断是新策略还是旧策略
            if avg_annual_return > 0.025:
                print('\n✅ 这是新策略的结果（平均年化收益率 > 2.5%）')
            else:
                print('\n⚠️  这是旧策略的结果（平均年化收益率 < 2.5%）')
    else:
        print(f'API请求失败: {response.status_code}')
        
except requests.exceptions.ConnectionError:
    print('❌ 无法连接到网页服务器')
    print('请先启动网页服务器：')
    print('  cd web && python3 app.py')
except Exception as e:
    print(f'❌ 发生错误: {e}')
