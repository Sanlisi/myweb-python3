drop database if exists sanlisi;
create database sanlisi;

use sanlisi;

grant select, insert, update, delete on sanlisi.* to 'g11303'@'localhost' identified by 'g11303';

create table users(
    `id` varchar(50) not null,
    `name` varchar(50) not null,
    `password` varchar(50) not null,
    `email` varchar(50) not null,
    `admin` bool not null,
    `image` varchar(500),
    `create_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_create_at` (`create_at`),
    primary key (`id`)
)engine = innodb default charset=utf8;

create table blogs(
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `name` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `create_at` real not null,
    key `idx_create_at` (`create_at`),
    primary key (`id`)
)engine=innodb default charset=utf8;

create table comments(
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `content` mediumtext not null,
    `create_at` real not null,
    key `idx_create_at` (`create_at`),
    primary key (`id`)
)engine=innodb default charset=utf8;
