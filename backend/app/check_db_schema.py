#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final.sql 변경사항 적용 여부 확인 스크립트
"""

import asyncio
from db.pool import execute_query

async def check_tables():
    """데이터베이스 테이블 구조 확인"""
    try:
        # 테이블 목록 확인
        tables = await execute_query('SHOW TABLES')
        print('=== 현재 데이터베이스 테이블 목록 ===')
        for table in tables:
            print(f'- {list(table.values())[0]}')
        
        print('\n=== humid 테이블 구조 확인 ===')
        humid_structure = await execute_query('DESCRIBE humid')
        for col in humid_structure:
            print(f'- {col["Field"]}: {col["Type"]} ({col["Null"]}, {col["Key"]})')
        
        print('\n=== humid_info 테이블 존재 여부 확인 ===')
        try:
            humid_info_check = await execute_query('SHOW TABLES LIKE "humid_info"')
            if humid_info_check:
                print('❌ humid_info 테이블이 아직 존재합니다!')
                print('   Final.sql 변경사항이 적용되지 않았습니다.')
            else:
                print('✅ humid_info 테이블이 삭제되었습니다.')
        except Exception as e:
            print(f'humid_info 테이블 확인 중 오류: {e}')
        
        print('\n=== device_info 테이블 존재 여부 확인 ===')
        try:
            device_info_check = await execute_query('SHOW TABLES LIKE "device_info"')
            if device_info_check:
                print('❌ device_info 테이블이 아직 존재합니다!')
                print('   Final.sql 변경사항이 적용되지 않았습니다.')
            else:
                print('✅ device_info 테이블이 삭제되었습니다.')
        except Exception as e:
            print(f'device_info 테이블 확인 중 오류: {e}')
        
        print('\n=== humid 테이블 데이터 확인 ===')
        humid_data = await execute_query('SELECT * FROM humid ORDER BY humid_date DESC LIMIT 5')
        if humid_data:
            print('최근 5개 습도 데이터:')
            for i, row in enumerate(humid_data, 1):
                print(f'  {i}. device_id={row["device_id"]}, humidity={row["humidity"]}%, sensor_digit={row["sensor_digit"]}, date={row["humid_date"]}')
        else:
            print('humid 테이블에 데이터가 없습니다.')
            
    except Exception as e:
        print(f'데이터베이스 확인 중 오류: {e}')

if __name__ == "__main__":
    asyncio.run(check_tables())
