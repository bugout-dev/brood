# brood

Bugout authentication

### Setup:
* Clone git repository
* Install postgresql (https://www.postgresql.org/download/linux/ubuntu/)
* Install requirements
* Copy sample.env to dev.env
* Copy alembic.sample.ini to alembic.dev.ini
* Edit variable "sqlalchemy.url = <...>" into alembic.dev.ini
* Run alembic
```
> ./alembic.sh -c alembic.dev.ini upgrade head
```
* Edit in dev.env file BROOD_DB_URI and BROOD_SENDGRID_API_KEY variable. BROOD_SENDGRID_API_KEY you can get in password vault.
* Last command befor start:
```
> source dev.env
```

### Start server:
```
> ./dev.sh

```

### CLI

#### Groups
* Create new group with specified `--name` and `--username` as an owner
```bash
python -m brood.cli groups create --name "bugout-group" --username "neeraj"
```
* Add user to group with specified `--name` as `group_name`, `--username` and `--type` as `member`/`owner`
```bash
python -m brood.cli groups role --name "bugout-group" --username "tim" --type "member" | jq .
```
