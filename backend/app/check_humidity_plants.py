#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
습도 정보와 습도계에 매칭된 식물 조회 스크립트
"""

import asyncio
import sys
import os

# 백엔드 앱 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.pool import execute_query, execute_one

async def get_humidity_plant_mapping():
    """습도 정보와 매칭된 식물 조회"""
    try:
        # 습도 정보 조회 쿼리 (humid 테이블 사용, device_id=1 공통)
        query = """
        SELECT 
            h.device_id,
            h.humidity,
            h.sensor_digit,
            h.humid_date,
            '공통' as plant_id,
            '모든 식물' as plant_name,
            '공통 센서' as location,
            '공통 데이터' as species,
            '시스템' as user_nickname
        FROM humid h
        WHERE h.device_id = 1
        ORDER BY h.humid_date DESC
        LIMIT 50
        """
        
        results = await execute_query(query)
        
        if not results:
            print("📊 습도 데이터가 없습니다.")
            return
        
        print("=" * 80)
        print("🌡️  습도 정보와 매칭된 식물 목록")
        print("=" * 80)
        
        for i, row in enumerate(results, 1):
            print(f"\n[{i}] 디바이스 ID: {row['device_id']}")
            print(f"    습도: {row['humidity']}%")
            print(f"    센서 값: {row['sensor_digit']}")
            print(f"    측정 시간: {row['humid_date']}")
            print(f"    식물 ID: {row['plant_id']}")
            print(f"    식물명: {row['plant_name']}")
            print(f"    위치: {row['location'] or '미설정'}")
            print(f"    종류: {row['species'] or '미분류'}")
            print(f"    사용자: {row['user_nickname']}")
            print("-" * 60)
        
        # 통계 정보
        print(f"\n📈 총 {len(results)}개의 습도 데이터")
        
        # 최근 24시간 내 데이터
        recent_query = """
        SELECT COUNT(*) as recent_count
        FROM humid_info hi
        JOIN device_info di ON hi.device_id = di.device_id
        WHERE hi.humid_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        recent_result = await execute_one(recent_query)
        recent_count = recent_result['recent_count'] if recent_result else 0
        print(f"📅 최근 24시간 내 데이터: {recent_count}개")
        
        # 평균 습도
        avg_query = """
        SELECT AVG(hi.humidity) as avg_humidity
        FROM humid_info hi
        JOIN device_info di ON hi.device_id = di.device_id
        WHERE hi.humid_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        avg_result = await execute_one(avg_query)
        if avg_result and avg_result['avg_humidity']:
            print(f"📊 최근 7일 평균 습도: {avg_result['avg_humidity']:.1f}%")
        
    except Exception as e:
        print(f"❌ 쿼리 실행 오류: {e}")

async def get_device_plant_summary():
    """디바이스별 식물 매칭 요약"""
    try:
        query = """
        SELECT 
            di.device_id,
            up.plant_name,
            up.species,
            u.nickname as user_nickname,
            COUNT(hi.humidity) as humidity_count,
            MAX(hi.humid_date) as last_measurement,
            AVG(hi.humidity) as avg_humidity
        FROM device_info di
        JOIN user_plant up ON di.plant_id = up.plant_id
        JOIN users u ON up.user_id = u.user_id
        LEFT JOIN humid_info hi ON di.device_id = hi.device_id
        GROUP BY di.device_id, up.plant_id
        ORDER BY di.device_id
        """
        
        results = await execute_query(query)
        
        print("\n" + "=" * 80)
        print("📱 디바이스별 식물 매칭 요약")
        print("=" * 80)
        
        for row in results:
            print(f"\n🔌 디바이스 ID: {row['device_id']}")
            print(f"   🌱 식물: {row['plant_name']} ({row['species'] or '미분류'})")
            print(f"   👤 사용자: {row['user_nickname']}")
            print(f"   📊 습도 측정 횟수: {row['humidity_count']}회")
            print(f"   📅 마지막 측정: {row['last_measurement'] or '측정 없음'}")
            if row['avg_humidity']:
                print(f"   📈 평균 습도: {row['avg_humidity']:.1f}%")
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ 쿼리 실행 오류: {e}")

async def main():
    """메인 함수"""
    print("🌡️  습도 정보와 식물 매칭 조회 시작")
    print("=" * 50)
    
    # 1. 습도 정보와 매칭된 식물 조회
    await get_humidity_plant_mapping()
    
    # 2. 디바이스별 식물 매칭 요약
    await get_device_plant_summary()
    
    print("\n✅ 조회 완료!")

if __name__ == "__main__":
    asyncio.run(main())
