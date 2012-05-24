drop table if exists shopdata;

create table shopdata (
    id integer primary key autoincrement,
    shopname string not null,
    shopprice integer not null,
    shopdes string not null,
    shopstar integer not null,
    tag string not null
);
