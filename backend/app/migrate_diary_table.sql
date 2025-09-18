-- 일기 테이블 마이그레이션 스크립트
-- 기존 diary 테이블을 새로운 구조로 업데이트

USE Final;

-- 기존 테이블 백업 (선택사항)
-- CREATE TABLE diary_backup AS SELECT * FROM diary;

-- 기존 diary 테이블 삭제 (주의: 데이터 손실)
-- DROP TABLE diary;

-- 새로운 diary 테이블 생성
CREATE TABLE diary (
    idx int auto_increment primary key,
    user_id varchar(100) not null,
    user_title varchar(500) not null,
    img_url varchar(300),
    user_content text,
    hashtag varchar(1000),
    plant_nickname varchar(100),
    plant_species varchar(100),
    plant_reply text,
    weather varchar(50),
    weather_icon varchar(300),
    created_at datetime,
    updated_at datetime,
    
    foreign key (user_id) references users(user_id) on delete cascade on update cascade
);

-- 기존 데이터가 있다면 마이그레이션 (plant_content -> plant_reply로 이동)
-- INSERT INTO diary (user_id, user_title, img_url, user_content, hashtag, plant_reply, weather, created_at, updated_at)
-- SELECT user_id, user_title, img_url, user_content, hashtag, plant_content, weather, created_at, created_at
-- FROM diary_backup;

-- 인덱스 추가 (성능 최적화)
CREATE INDEX idx_diary_user_id ON diary(user_id);
CREATE INDEX idx_diary_created_at ON diary(created_at);
CREATE INDEX idx_diary_plant_species ON diary(plant_species);
