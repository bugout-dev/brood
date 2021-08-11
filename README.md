# bugout-dev/brood

## What is Brood?

Sympathy: Difficulty with -

1. User management
2. Team management
3. Payments

Brood is a web service that gives you all this functionality as soon as you set it up.

Brood is a free and open source alternative to systems like AWS Cognito and Auth0 which also supports
payments.

How it works:

- Postgres database
- Sets up tables
- Manages all the authentication + payment logic
- Everything exposed via a REST API

Battle tested - e.g. https://bugout.dev, https://moonstream.to.

## Running Brood

### Setup:

- Clone git repository
- Install postgresql (https://www.postgresql.org/download/linux/ubuntu/)
- Install requirements
- Copy sample.env to dev.env
- Copy alembic.sample.ini to alembic.dev.ini
- Edit variable "sqlalchemy.url = <...>" into alembic.dev.ini
- Run alembic

```
> ./alembic.sh -c alembic.dev.ini upgrade head
```

- Edit in dev.env file BROOD_DB_URI and BROOD_SENDGRID_API_KEY variable. BROOD_SENDGRID_API_KEY you can get in password vault.
- Last command befor start:

```
> source dev.env
```

### Start server:

```
> ./dev.sh

```

### CLI

#### Groups

- Create new group with specified `--name` and `--username` as an owner

```bash
python -m brood.cli groups create --name "bugout-group" --username "neeraj"
```

- Add user to group with specified `--name` as `group_name`, `--username` and `--type` as `member`/`owner`

```bash
python -m brood.cli groups role --name "bugout-group" --username "tim" --type "member" | jq .
```
