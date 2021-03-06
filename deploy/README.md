# Deploy LocalEGA using Docker

## Bootstrap

You can then [generate the private data](bootstrap), with:

	make -C bootstrap

This requires `openssl` (>=1.1), `ssh-keygen` (=>6.5).  
Install the required python packages with `pip install -r bootstrap/requirements.txt`.

Bootstrapping will create a `.env` file and a `private` directory
holding the necessary data (ie the master keypair, the TLS
certificates for internal communication, passwords, default users,
configuration files, etc...)

The passwords are in `private/secrets` and the errors (if any) are in `private/.err`.

The credentials for the test users are found in `private/users`.

## Convenient commands

| Makefile targets | Shortcut for | Notes |
|:----------------:|:-------------|:------|
| make up          | `docker-compose up -d` | Use `docker-compose up -d --scale ingest=3 --scale verify=5` instead, if you want to start 3 ingestion and 5 verification workers. |
| make down        | `docker-compose down -v` | `-v`: removing networks and volumes |
| make ps          | `docker-compose ps` | |

Note that, in this architecture, we use separate volumes, e.g. for the
inbox area, for the archive (be it a POSIX file system or backed by
S3). They will be created on-the-fly by docker-compose.

----

# LocalEGA docker image

Create the base image by executing:

	make image

It takes some time. The result is an image, named `egarchive/lega-base`, and containing `python 3.6` and the LocalEGA services.

The following images are pulled from Docker Hub, when starting LocalEGA (only the first time, if not present):

* [`egarchive/lega-mq`](https://github.com/EGA-archive/LocalEGA-mq) (based on `rabbitmq:3.6.14-management`)
* [`egarchive/lega-db`](https://github.com/EGA-archive/LocalEGA-db) (based on `postgres:11.2`)
* [`egarchive/lega-inbox`](https://github.com/EGA-archive/LocalEGA-inbox) (based on OpenSSH version 7.8p1 and CentOS7)
* `python:3.8-alpine3.11` 


> Important notice: The user inside the container is called `lega`,
> and its ID is by default 1000. When (re)building the image, the
> above target `make image` will make the ID match the current user
> calling the command. This is important to allow injected files to be
> readable by the `lega` user inside the containers.

----

# Fake Central EGA

We use 2 stubbing services in order to fake the necessary Central EGA components (mostly for local or Travis tests).

| Container    | Role |
|-------------:|------|
| `cega-users` | Sets up a small list of test users |
| `cega-mq`    | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |

If the `cega-users` is not built, it will be build by docker-compose. If you want to build yourself, you can run:

	docker-compose build cega-users
