# bugout-dev/brood

## What is Brood?

Setting up user registration and login in your application can be challenging and time consuming.
Doing this from scratch takes a lot of planning. Since you're working with sensitive data (emails,
passwords) it's important not to get it wrong.

Giving users the ability to set up groups or teams within which they can share resources adds to this
challenge, and adding payments compounds it significantly.

Brood is a web service that takes care of user management, team management, and payments in your
application as soon as you set it up.

It is a free and open source alternative to systems like AWS Cognito and Auth0.

Brood provides a REST API that you can use either directly from your frontend application or through
your own API or serverless application. It uses a Postgres database to store data about users,
teams, and payments.

Payments are currently supported through Stripe.

Brood has been battle tested in production and has been supporting millions of authentication events
a month since March 2021.

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
