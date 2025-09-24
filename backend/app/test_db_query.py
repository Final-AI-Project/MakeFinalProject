"""
DB 쿼리 테스트 스크립트
백엔드에서 품종별 습도 범위 데이터를 가져오는 방식을 테스트합니다.
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.pool import get_db_connection

async def test_db_query():
    """DB 쿼리 테스트"""
    try:
        async with get_db_connection() as (conn, cursor):
            print("=== DB 연결 성공 ===")
            
            # 1. user_plant 테이블 확인
            await cursor.execute("SELECT COUNT(*) as count FROM user_plant")
            user_plant_count = await cursor.fetchone()
            print(f"user_plant 테이블: {user_plant_count['count']}개 레코드")
            
            # 2. plant_wiki 테이블 확인
            await cursor.execute("SELECT COUNT(*) as count FROM plant_wiki")
            wiki_count = await cursor.fetchone()
            print(f"plant_wiki 테이블: {wiki_count['count']}개 레코드")
            
            # 3. best_humid 테이블 확인
            await cursor.execute("SELECT COUNT(*) as count FROM best_humid")
            humid_count = await cursor.fetchone()
            print(f"best_humid 테이블: {humid_count['count']}개 레코드")
            
            print("\n=== 샘플 데이터 확인 ===")
            
            # 4. user_plant 샘플 데이터
            await cursor.execute("SELECT plant_id, plant_name, species FROM user_plant LIMIT 5")
            user_plants = await cursor.fetchall()
            print("user_plant 샘플:")
            for plant in user_plants:
                print(f"  - ID: {plant['plant_id']}, 이름: {plant['plant_name']}, 품종: {plant['species']}")
            
            # 5. plant_wiki 샘플 데이터
            await cursor.execute("SELECT wiki_plant_id, name_jong, sci_name FROM plant_wiki LIMIT 5")
            wiki_plants = await cursor.fetchall()
            print("\nplant_wiki 샘플:")
            for wiki in wiki_plants:
                print(f"  - ID: {wiki['wiki_plant_id']}, 한글명: {wiki['name_jong']}, 학명: {wiki['sci_name']}")
            
            # 6. best_humid 샘플 데이터
            await cursor.execute("SELECT wiki_plant_id, min_humid, max_humid FROM best_humid LIMIT 5")
            humid_data = await cursor.fetchall()
            print("\nbest_humid 샘플:")
            for humid in humid_data:
                print(f"  - wiki_plant_id: {humid['wiki_plant_id']}, 범위: {humid['min_humid']}-{humid['max_humid']}%")
            
            print("\n=== 조인 테스트 ===")
            
            # 7. 실제 대시보드 쿼리 테스트 (단어 포함식 매칭)
            query = """
            SELECT 
                up.plant_id,
                up.plant_name,
                up.species,
                pw.name_jong,
                pw.wiki_plant_id,
                pw.sci_name,
                bh.min_humid,
                bh.max_humid
            FROM user_plant up
            LEFT JOIN plant_wiki pw ON (
                pw.sci_name LIKE CONCAT('%', up.species, '%')
                OR up.species LIKE CONCAT('%', TRIM(SUBSTRING_INDEX(pw.sci_name, '(', 1)), '%')
            )
            LEFT JOIN best_humid bh ON pw.wiki_plant_id = bh.wiki_plant_id
            LIMIT 10
            """
            
            await cursor.execute(query)
            results = await cursor.fetchall()
            
            print("조인 결과:")
            for i, row in enumerate(results, 1):
                print(f"  {i}. 식물: {row['plant_name']} ({row['species']})")
                print(f"     → 위키 매칭: {row['name_jong']} (ID: {row['wiki_plant_id']})")
                print(f"     → 습도 범위: {row['min_humid']}-{row['max_humid']}%")
                print(f"     → 매칭 상태: {'✅ 성공' if row['min_humid'] else '❌ 실패'}")
                print()
            
            # 8. 매칭 실패한 품종들 확인
            print("=== 매칭 실패한 품종들 ===")
            await cursor.execute("""
                SELECT DISTINCT up.species
                FROM user_plant up
                LEFT JOIN plant_wiki pw ON up.species = pw.name_jong
                WHERE pw.name_jong IS NULL
            """)
            failed_matches = await cursor.fetchall()
            
            if failed_matches:
                print("매칭되지 않은 품종들:")
                for match in failed_matches:
                    print(f"  - {match['species']}")
            else:
                print("모든 품종이 매칭되었습니다!")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_query())
