FROM pgvector/pgvector:pg18

ENV POSTGRES_USER myuser
ENV POSTGRES_PASSWORD mypassword
ENV POSTGRES_DB vectordb

COPY ./backup.sql /docker-entrypoint-initdb.d/backup.sql

EXPOSE 5432