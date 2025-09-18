use Final;

create table users (
	idx int auto_increment primary key,
    user_id varchar(100) not null unique,
    user_pw varchar(255) not null,
    email varchar(50) not null unique,
    hp varchar(20) not null unique,
    nickname varchar(20) not null,
    regdate datetime default now()
);

create table user_plant (
	idx int auto_increment primary key,
    user_id varchar(100) not null,
    plant_id int not null unique,
    plant_name varchar(100) not null,
    species varchar(100),
    pest_id int,
    meet_day datetime,
    
	foreign key (user_id) references users(user_id) on delete cascade on update cascade
);

-- pest_id : 병충해 ID
-- meet_day : 만난 날

create table diary (
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

-- user_title : 사용자가 직접 작성하는 일기 제목
-- user_content : 일기 내용
-- hashtag : 해시태그
-- plant_nickname : 식물별명
-- plant_species : 식물종류
-- plant_reply : LLM이 작성하는 식물의 답변
-- weather : 작성일 기준 날씨
-- weather_icon : 날씨 아이콘 URL
-- created_at : 작성일
-- updated_at : 수정일

create table pest_wiki (
	idx int auto_increment primary key,
    pest_id int not null,
    cause varchar(100) not null,
    cure text not null
);

create table humid_info (
	plant_id int not null,
    humidity float not null,
    humid_date datetime not null,
    
    foreign key (plant_id) references user_plant(plant_id) on delete cascade on update cascade
);

create table plant_wiki (
	idx int auto_increment primary key,
    name_jong varchar(300),
    name_sok varchar(300),
    name_gwa varchar(300),
    name_mok varchar(300),
    name_gang varchar(300),
    name_mun varchar(300),
    wiki_img varchar(300) not null,
    feature text,
    temp varchar(300),
    watering varchar(300),
    flowering varchar(300),
    flower_color varchar(300),
    flower_diam varchar(300),
    fertilizer varchar(300),
    pruning varchar(300),
    repot varchar(300),
    toxic varchar(300)
);

-- watering : 급수 주기
-- flowering : 개화 시기
-- fertilizer : 비료 주기
-- toxic : 사람이나 반려동물에게 유독한 성분의 여부

create table img_address (
	idx int auto_increment primary key,
    diary_id int not null,
    img_url varchar(300),
    
    foreign key (diary_id) references diary(diary_id) on delete cascade on update cascade
);

drop table users;
drop table user_plant;
drop table diary;
drop table pest_wiki;
drop table humid_info;
drop table plant_wiki;
drop table img_address;

-- users.user_id 와 user_plant.user_id join으로 사용자의 식물 조회
select u.user_id, u.nickname, up.plant_id, up.plant_name, up.species, up.meet_day from users u join user_plant up on u.user_id = up.user_id;

-- diary.img_url 와 img_address.img_url join으로 식물 이미지 조회
select d.diary_id, d.user_id, ia.img_url from diary d join img_address ia on d.diary_id = ia.diary_id;