drop table if exists account;

create table account (
    id integer primary key autoincrement,
    username string not null,
    password string not null,
    shopcart string default ''
);
