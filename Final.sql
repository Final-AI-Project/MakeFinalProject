set names utf8mb4;
set time_zone = '+09:00';
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
	plant_id int auto_increment primary key,
    user_id varchar(100) not null,
    plant_name varchar(100) not null,
    location varchar(300),
    species varchar(100),
    meet_day date,
	foreign key (user_id) references users(user_id) on delete cascade on update cascade
);
SET SQL_SAFE_UPDATES = 1;
DELETE FROM user_plant
WHERE plant_name = '더미마이플랜트';
create table user_plant_pest (
	idx int auto_increment primary key,
    plant_id int not null,
    pest_id int not null,
    pest_date date,
    foreign key (plant_id) references user_plant(plant_id) on delete cascade on update cascade,
    foreign key (pest_id) references pest_wiki(pest_id) on delete cascade on update cascade
);
create table diary (
	diary_id int auto_increment primary key,
    user_id varchar(100) not null,
    user_title varchar(500) not null,
    user_content text,
    hashtag varchar(1000),
    plant_id int,
    plant_content text,
    weather varchar(30),
    hist_watered tinyint,
    hist_repot tinyint,
    hist_pruning tinyint,
    hist_fertilize tinyint,
    created_at date,
    foreign key (user_id) references users(user_id) on delete cascade on update cascade,
    foreign key (plant_id) references user_plant(plant_id) on delete cascade on update cascade
);
create table pest_wiki (
	pest_id int auto_increment primary key,
    pest_name varchar(100) not null,
    pathogen varchar(300),
    symptom text not null,
    cure text not null
);
create table plant_wiki (
	wiki_plant_id int auto_increment primary key,
    sci_name varchar(100),
    name_jong varchar(300),
    name_sok varchar(30),
    name_gwa varchar(30),
    name_mok varchar(30),
    name_gang varchar(30),
    name_mun varchar(30),
    feature text,
    temp varchar(30),
    watering varchar(300),
    flowering varchar(300),
    flower_color varchar(300),
    flower_diam varchar(300),
    fertilizer varchar(300),
    pruning varchar(300),
    repot varchar(300),
    toxic varchar(300)
);
create table plant_tips (
	idx int auto_increment primary key,
    wiki_plant_id int not null,
    tip text,
    foreign key (wiki_plant_id) references plant_wiki(wiki_plant_id) on delete cascade on update cascade
);
create table img_address (
    diary_id int,
    plant_id int,
    wiki_plant_id int,
    pest_id int,
    pest_plant_idx int,
    img_url varchar(300) not null,
    foreign key (diary_id) references diary(diary_id) on delete cascade on update cascade,
    foreign key (plant_id) references user_plant(plant_id) on delete cascade on update cascade,
    foreign key (wiki_plant_id) references plant_wiki(wiki_plant_id) on delete cascade on update cascade,
    foreign key (pest_plant_idx)references user_plant_pest(idx) on delete cascade on update cascade,
    foreign key (pest_id) references pest_wiki(pest_id) on delete cascade on update cascade
);
create table best_humid (
	wiki_plant_id int,
    min_humid int,
    max_humid int,
    foreign key (wiki_plant_id) references plant_wiki(wiki_plant_id) on delete cascade on update cascade
);
create table best_humid_cali (
	wiki_plant_id int,
    min_humid int,
    max_humid int,
    foreign key (wiki_plant_id) references plant_wiki(wiki_plant_id) on delete cascade on update cascade
);

create table humid (
	idx int auto_increment primary key,
	device_id int not null,
    humidity int not null,
    sensor_digit int not null,
    humid_date datetime default now()
);
