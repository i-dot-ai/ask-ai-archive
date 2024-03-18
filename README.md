# Ask AI

**This repo is an archive - the project is no longer being maintained.**

This is a Django project to build an internal interface to generative AI for internal use within the Cabinet Office. The purpose of the interface is to save user queries to generative AI and their responses, and flag sensitive material. This is to ensure no sensitive material is uploaded to ChatGPT (or similar), and for audit purposes.


## Minimum viable product

* Allow users to query ChatGPT (GPT3.5 model)
* Basic checking to flag sensitive material and block inappropriate material
* Save queries and responses to database
* Login using COLA (Cabinet Office Login App(?))


## Phase - private beta

Ask AI is currently in private beta. We have invited a limited number of people within the Cabinet Office to try out the the product. This enables us to get feedback and improve it.


## To run locally

Clone the repo.

Add a `.env` file in the root of the directory - you can copy the `.env.example` template. You will need to add a working API key for the `OPENAI_KEY`:
```
OPENAI_KEY=<MY_OPENAI_KEY>
```
Do not commit this file or key (it is in the `.gitignore`).

Now run in Docker:
```
docker-compose up --build --force-recreate web
```

Note: Docker set-up for running locally ONLY (not set-up for production e.g. uses `python manage.py runserver`).

Or without Docker:
```
poetry run python manage.py runserver
```

In the browser go to:
```
http://localhost:8000
```

To login locally, we don't have a substitute for COLA - so login using the Django admin.

Create a superuser:
```
docker-compose run web poetry run python manage.py createsuperuser
```

Then login via:
```
http://localhost:8000/admin/
```

## Environment variables running locally and for testing

When running locally, you will need to create a `.env` file. This may contain sensitive data, for example, an Open AI API key. This should not be committed to Git.

There is a sample version of this file `.env.example` that you can copy. This file is committed to the repo, so don't put anything sensitive in there.

Environment variables for running tests are stored in `.env.test`. Again, this file is committed to the repo, so shouldn't contain anything sensitive.

Make sure you update the `.env.example` and `.env.test` files with any new environment variables that you add.


## Login & user management

We are using COLA, the Cabinet Office Login App to allow people to login and for user management.

See the i.AI team wiki for details on COLA set-up.

For login locally, create a superuser and login via the admin.

We are only exposing the admin when running locally. This is so we keep all user management in COLA.


## Data download

Users need to have the `data-download` feature set on COLA to download data on chats. This is for audit purposes.

This view can be found at `/data-download/`.

Locally, this feature maps to the permission group, "Data download" which you can set in the Django admin if testing locally.


## To run tests

1. In Docker, as used in CI:
```commandline
make test
```

2. Locally, e.g. so you can debug in an IDE
```commandline
docker-compose up -d db
poetry run pytest tests -v --cov=ask_ai --cov-fail-under 92
```

## Pre-commit hooks

Pre-commit hooks will be run whenever a commit is made, they can also be run manually using the following commands.

To install the pre-commit hooks required code:

`poetry run pre-commit install`

To re-generate the detect-secrets baseline file:

`poetry run detect-secrets scan --baseline .secrets.baseline`

Information about detect-secrets can be found in this repo [https://github.com/Yelp/detect-secrets](https://github.com/Yelp/detect-secrets)

To run the pre-commit hook manually:

`poetry run pre-commit run --all-files`

Usually pre-commit runs on all changes to files on each commit.

Information about pre-commit can be found here [https://pre-commit.com/](https://pre-commit.com/)
