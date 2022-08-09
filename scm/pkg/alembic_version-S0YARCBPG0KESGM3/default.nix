stdargs @ { scm, ... }:

scm.schema {
    guid = "S0YARCBPG0KESGM3";
    name = "alembic_version";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-alembic_version-R001COQ5I1VO0W4K>
    ];
}
