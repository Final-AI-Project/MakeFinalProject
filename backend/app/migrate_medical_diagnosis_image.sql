-- 병충해 진단 테이블에 이미지 URL 컬럼 추가
-- 실행 전 백업 권장

-- user_plant_pest 테이블에 diagnosis_image_url 컬럼 추가
ALTER TABLE user_plant_pest 
ADD COLUMN diagnosis_image_url VARCHAR(500) NULL 
COMMENT '진단 시 찍은 사진 URL';

-- 인덱스 추가 (선택사항 - 이미지 URL로 검색할 경우)
-- CREATE INDEX idx_user_plant_pest_image_url ON user_plant_pest(diagnosis_image_url);

-- 기존 데이터 확인
SELECT 
    COUNT(*) as total_records,
    COUNT(diagnosis_image_url) as records_with_image
FROM user_plant_pest;

-- 마이그레이션 완료 확인
DESCRIBE user_plant_pest;
