# bugout-dev/brood

## What is Brood?

Setting up user registration and login in your application can be challenging and time consuming.
Doing this from scratch takes a lot of planning. Since you're working with sensitive data (emails,
passwords, etc) it's important not to get it wrong.

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

## Using Brood

To get started with Brood, we'll first need to create a user. This represents a user of your application.
Creating a user is as simple as `POST`ing a form:

```bash
curl -X POST https://auth.bugout.dev/user \
    -F "username=pepper" \
    -F "email=pepper@example.com" \
    -F "password=1dc23a784ed36056887ef0967e8431817a1a2d9e2b3938eef0d0c9d0227d7c14"
```

You can also create a user using one of our client libraries. For example, in Javascript:

```javascript
import BugoutClient, { BugoutTypes } from "@bugout/bugout-js";
const bugout = new BugoutClient();

bugout
  .createUser(
    "pepper",
    "pepper@example.com",
    "1dc23a784ed36056887ef0967e8431817a1a2d9e2b3938eef0d0c9d0227d7c14",
    "Pepper",
    "Cat"
  )
  .then(console.log)
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
```

Each user is identified to Brood using access tokens in the authorization header of Brood requests.
The authorization header should have the form `Authorization: Bearer <access_token>`.

If you are integrating Brood into your own API or serverless application, you can just pass this header
through to Brood when you are working with Brood resources and it will handle permissions on your
behalf with no hassles.

To generate an access token for a user, you again `POST` a form:

```bash
curl -X POST https://auth.bugout.dev/token \
    -F "username=pepper" \
    -F "password=1dc23a784ed36056887ef0967e8431817a1a2d9e2b3938eef0d0c9d0227d7c14"
```

In Javascript:

```javascript
import BugoutClient, { BugoutTypes } from "@bugout/bugout-js";
const bugout = new BugoutClient();

bugout
  .createToken(
    "pepper",
    "1dc23a784ed36056887ef0967e8431817a1a2d9e2b3938eef0d0c9d0227d7c14"
  )
  .then(console.log)
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
```

### CORS configuration

If you are using Brood directly from your frontend, you will need to configure the Brood server to
respond to CORS requests from your users' browsers. This is actually very simple. When you start
your Brood servers, simply set the following environment variable:

```bash
BROOD_CORS_ALLOWED_ORIGINS="<domain at which your site is hosted>"
```

For example, if your frontend lives at `https://frontend.example.com`, then you would set:

```bash
BROOD_CORS_ALLOWED_ORIGINS="https://frontend.example.com"
```

You can pass multiple domains as a comma-separated list. If you had sites at `https://frontend.example.com`
and at `https://other-frontend.example.com`, you would set:

```bash
BROOD_CORS_ALLOWED_ORIGINS="https://frontend.example.com,https://other-frontend.example.com"
```

In your development environment, you can set a localhost domain as follows:

```bash
BROOD_CORS_ALLOWED_ORIGINS="http://localhost:3000"
```

### Client libraries

To make coding against the Brood API easier, you can use one of the client libraries:

- [Javascript](https://www.npmjs.com/package/@bugout/bugout-js)
- [Python](https://pypi.org/project/bugout/)
- [Go](https://github.com/bugout-dev/bugout-go)

### API documentation

You can find a more detailed documentation on the API [here](https://auth.bugout.dev/docs)

## Running Brood

### Installation and setup

To set up Brood for development, do the following:

- Clone the git repository
- Install postgresql (https://www.postgresql.org/download/linux/ubuntu/)
<!-- these will probably need explanations or screenshots -->

#### Run server from terminal

- Install requirements

```bash
pip install -e .[dev]
```

- Copy `configs/alembic.sample.ini` to `configs/alembic.dev.ini`
- Edit variable `sqlalchemy.url = <...>` into `alembic.dev.ini`
- Copy `configs/sample.env` to `configs/dev.env`
- Edit in `dev.env` file BROOD_DB_URI and other variables.
- Source environment variables

```
source configs/dev.env
```

- Run alembic migration

```
./alembic.sh -c configs/alembic.dev.ini upgrade head
```

Once you're ready with the installation, start the server:

```
./dev.sh
```

#### Run server with Docker

To be able to run Brood with your existing local or development services as database, you need to build your own setup. **Be aware! The files with environment variables `docker.dev.env` lives inside your docker container!**

- Copy `configs/sample.env` to `configs/docker.dev.env`, or use your local configs from `configs/dev.env` to `configs/docker.dev.env`
- Edit in `docker.dev.env` file `BROOD_DB_URI` and other variables if required
- Clean environment file from `export ` prefix and quotation marks to be able to use it with Docker

```bash
sed --in-place 's|^export * ||' configs/docker.dev.env
sed --in-place 's|"||g' configs/docker.dev.env
```

Build container on your machine

```bash
docker build -t brood-dev .
```

Run `brood-dev` container, with following command we specified `--network="host"` setting which allows to Docker container use localhost interface of your machine (https://docs.docker.com/network/host/)

```bash
docker run --name brood-dev \
  --network="host" \
  --env-file="configs/docker.dev.env" \
  -p 7474:7474/tcp \
  -ti -d brood-dev
```

Attach to container to see logs

```bash
docker container attach brood-dev
```

#### Run server with Docker Compose

If you want to deploy Brood in isolation against live services, then docker compose is your choice!

- Run script `configs/docker_generate_env.bash` which prepare for you:
  - `configs/docker.brood.env` with environment variables
  - `configs/alembic.brood.ini` with postgresql uri

```bash
./configs/docker_generate_env.bash
```

- Run local setup

```bash
docker-compose up --build
```

### After setup

Fresh server is not fully functional, in order to add additional functionality you need to create subscriptions, resources and etc.

#### Groups

To be able to create new groups, free subscription plan should be generated with record in kv_brood table:

```bash
python -m brood.cli plans create \
  --name "Free plan" \
  --description "free plan description" \
  --default_units 5 \
  --plan_type "seats" \
  --public True \
  --kv_key BUGOUT_GROUP_FREE_SUBSCRIPTION_PLAN
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
