FROM mariadb:11.4

LABEL version="1.0"

# On the first start (empty data volume) the official image creates the
# database and the app user from these variables. The tables themselves are
# created by the backend from the ORM models (schema.sql is reference only).
# Credentials are hard-coded for now (internal use only): root/aura, aura/aura.
ENV MARIADB_ROOT_PASSWORD=aura \
    MARIADB_DATABASE=si_hospitalier_db \
    MARIADB_USER=aura \
    MARIADB_PASSWORD=aura

# Server defaults: utf8mb4 everywhere, matching the schema.
RUN printf '[mariadbd]\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci\n' \
    > /etc/mysql/conf.d/charset.cnf

VOLUME /var/lib/mysql
EXPOSE 3306

HEALTHCHECK --start-period=30s --interval=10s --timeout=5s --retries=5 \
    CMD healthcheck.sh --connect --innodb_initialized || exit 1
