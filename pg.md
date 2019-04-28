
# PostgreSQL 支持

## Step1. 本地部署客户端

```bash
docker pull dpage/pgadmin4

docker run -d -p 8080:80 -e "PGADMIN_DEFAULT_EMAIL=xiaolong@caicloud.io" -e "PGADMIN_DEFAULT_PASSWORD=admin" dpage/pgadmin4
```

## Step2. 服务端部署

```bash
docker pull postgres:11.2-alpine

docker run -e POSTGRES_DB=website \
  -e POSTGRES_USER=k8smeetup \
  -e POSTGRES_PASSWORD=caicloud.io \
  -v `pwd`/pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  -d postgres:11.2-alpine
```

```sql
CREATE USER k8s WITH
  LOGIN
  SUPERUSER
  INHERIT
  CREATEDB
  CREATEROLE
  REPLICATION;
ALTER USER k8s
	PASSWORD 'kubernetes';
CREATE DATABASE website
    WITH
    OWNER = k8s
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- 清除所有的数据表
CREATE OR REPLACE FUNCTION truncate_tables(username IN VARCHAR) RETURNS void AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE tableowner = username AND schemaname = 'public';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'DROP TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

SELECT truncate_tables('k8smeetup');

alter table taskfiles add constraint unique_files_version unique(files,version);
```