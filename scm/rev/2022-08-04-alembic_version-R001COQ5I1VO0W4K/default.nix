stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COQ5I1VO0W4K";
    name = "2022-08-04-alembic_version";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}
