-- user_plant_pest 테이블 수정: 여러 진단 결과 저장 가능하도록
-- 1. 기존 UNIQUE 제약 조건 제거
ALTER TABLE user_plant_pest DROP INDEX plant_id;
ALTER TABLE user_plant_pest DROP INDEX pest_id;

-- 2. 새로운 복합 인덱스 추가 (성능 최적화)
ALTER TABLE user_plant_pest ADD INDEX idx_plant_date (plant_id, pest_date);

-- 3. 테이블 구조 확인
DESCRIBE user_plant_pest;
