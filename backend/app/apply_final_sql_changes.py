#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final.sql 변경사항을 데이터베이스에 적용하는 스크립트
"""

import asyncio
from db.pool import get_db_connection

async def apply_final_sql_changes():
    """Final.sql 변경사항 적용"""
    try:
        async with get_db_connection() as (conn, cursor):
            print("=== Final.sql 변경사항 적용 시작 ===")
            
            # 1. humid_info 테이블 삭제
            print("\n1. humid_info 테이블 삭제 중...")
            try:
                await cursor.execute("DROP TABLE IF EXISTS humid_info")
                await conn.commit()
                print("✅ humid_info 테이블 삭제 완료")
            except Exception as e:
                print(f"❌ humid_info 테이블 삭제 실패: {e}")
            
            # 2. device_info 테이블 삭제
            print("\n2. device_info 테이블 삭제 중...")
            try:
                await cursor.execute("DROP TABLE IF EXISTS device_info")
                await conn.commit()
                print("✅ device_info 테이블 삭제 완료")
            except Exception as e:
                print(f"❌ device_info 테이블 삭제 실패: {e}")
            
            # 3. 변경사항 확인
            print("\n3. 변경사항 확인 중...")
            tables = await cursor.execute("SHOW TABLES")
            table_list = await cursor.fetchall()
            
            print("\n=== 현재 테이블 목록 ===")
            for table in table_list:
                print(f"- {list(table.values())[0]}")
            
            # 4. humid 테이블 데이터 확인
            print("\n4. humid 테이블 데이터 확인...")
            await cursor.execute("SELECT COUNT(*) as count FROM humid")
            count_result = await cursor.fetchone()
            print(f"humid 테이블 데이터 개수: {count_result['count']}개")
            
            if count_result['count'] > 0:
                await cursor.execute("SELECT * FROM humid ORDER BY humid_date DESC LIMIT 3")
                recent_data = await cursor.fetchall()
                print("최근 3개 습도 데이터:")
                for i, row in enumerate(recent_data, 1):
                    print(f"  {i}. device_id={row['device_id']}, humidity={row['humidity']}%, date={row['humid_date']}")
            
            print("\n✅ Final.sql 변경사항 적용 완료!")
            
    except Exception as e:
        print(f"❌ 변경사항 적용 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(apply_final_sql_changes())
