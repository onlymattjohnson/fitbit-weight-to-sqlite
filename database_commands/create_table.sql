CREATE TABLE weight (
    id int primary key NOT NULL,
    date text not null,
    time text null,
    external_id int null,
    external_source_name text not null,
    device_name null,
    weight real not null
);