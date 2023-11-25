# PGN Bot

## Backend Requirements

* [Docker](https://www.docker.com/).
* [Docker Compose](https://docs.docker.com/compose/install/).
* [Poetry](https://python-poetry.org/) for Python package and environment management.

## Backend local development

* Start the stack with Docker Compose:

```bash
docker-compose up -d --build
```

Backend, JSON based web API based on OpenAPI: http://localhost/api/

Automatic interactive documentation with Swagger UI (from the OpenAPI backend): http://localhost/docs

Alternative automatic documentation with ReDoc (from the OpenAPI backend): http://localhost/redoc

Traefik UI, to see how the routes are being handled by the proxy: http://localhost:8090

**Note**: The first time you start your stack, it might take a minute for it to be ready. While the backend waits for the database to be ready and configures everything. You can check the logs to monitor it.

To check the logs, run:

```bash
docker-compose logs
```

To check the logs of a specific service, add the name of the service, e.g.:

```bash
docker-compose logs backend
```

If your Docker is not running in `localhost` (the URLs above wouldn't work) check the sections below on **Development with Docker Toolbox** and **Development with a custom IP**.

## Backend local development, additional details

### General workflow

By default, the dependencies are managed with [Poetry](https://python-poetry.org/), go there and install it.

From `./src/app/` you can install all the dependencies with:

```console
$ poetry install
```

Then you can start a shell session with the new environment with:

```console
$ poetry shell
```

Next, open your editor at `./src/app/` (instead of the project root: `./`), so that you see an `./app/` directory with your code inside. That way, your editor will be able to find all the imports, etc. Make sure your editor uses the environment you just created with Poetry.

### Docker Compose Override

During development, you can change Docker Compose settings that will only affect the local development environment, in the file `docker-compose.override.yml`.

The changes to that file only affect the local development environment, not the production environment. So, you can add "temporary" changes that help the development workflow.

For example, the directory with the backend code is mounted as a Docker "host volume", mapping the code you change live to the directory inside the container. That allows you to test your changes right away, without having to build the Docker image again. It should only be done during development, for production, you should build the Docker image with a recent version of the backend code. But during development, it allows you to iterate very fast.

There is also a command override that runs `/start-reload.sh` (included in the base image) instead of the default `/start.sh` (also included in the base image). It starts a single server process (instead of multiple, as would be for production) and reloads the process whenever the code changes. Have in mind that if you have a syntax error and save the Python file, it will break and exit, and the container will stop. After that, you can restart the container by fixing the error and running again:

```console
$ docker-compose up -d
```

There is also a commented out `command` override, you can uncomment it and comment the default one. It makes the backend container run a process that does "nothing", but keeps the container alive. That allows you to get inside your running container and execute commands inside, for example a Python interpreter to test installed dependencies, or start the development server that reloads when it detects changes, or start a Jupyter Notebook session.

To get inside the container with a `bash` session you can start the stack with:

```console
$ docker-compose up -d
```

and then `exec` inside the running container:

```console
$ docker-compose exec backend bash
```

You should see an output like:

```console
root@7f2607af31c3:/app#
```

that means that you are in a `bash` session inside your container, as a `root` user, under the `/app` directory.

There you can use the script `/start-reload.sh` to run the debug live reloading server. You can run that script from inside the container with:

```console
$ bash /start-reload.sh
```

...it will look like:

```console
root@7f2607af31c3:/app# bash /start-reload.sh
```

and then hit enter. That runs the live reloading server that auto reloads when it detects code changes.

Nevertheless, if it doesn't detect a change but a syntax error, it will just stop with an error. But as the container is still alive and you are in a Bash session, you can quickly restart it after fixing the error, running the same command ("up arrow" and "Enter").

...this previous detail is what makes it useful to have the container alive doing nothing and then, in a Bash session, make it run the live reload server.

## Deployment

You can deploy the stack to a Docker Swarm mode cluster with a main Traefik proxy, set up using the ideas from <a href="https://dockerswarm.rocks" target="_blank">DockerSwarm.rocks</a>, to get automatic HTTPS certificates, etc.

And you can use CI (continuous integration) systems to do it automatically.

But you have to configure a couple things first.

### Traefik network

This stack expects the public Traefik network to be named `traefik-public`, just as in the tutorials in <a href="https://dockerswarm.rocks" class="external-link" target="_blank">DockerSwarm.rocks</a>.

If you need to use a different Traefik public network name, update it in the `docker-compose.yml` files, in the section:

```YAML
networks:
  traefik-public:
    external: true
```

Change `traefik-public` to the name of the used Traefik network. And then update it in the file `.env`:

```bash
TRAEFIK_PUBLIC_NETWORK=traefik-public
```

### Deploy to a Docker Swarm mode cluster

There are 3 steps:

1. **Build** your app images
2. Optionally, **push** your custom images to a Docker Registry
3. **Deploy** your stack

---

Here are the steps in detail:

1. **Build your app images**

* Set these environment variables, right before the next command:
  * `TAG=prod`
* Use the provided `scripts/build.sh` file with those environment variables:

```bash
TAG=prod FRONTEND_ENV=production bash ./scripts/build.sh
```

2. **Optionally, push your images to a Docker Registry**

**Note**: if the deployment Docker Swarm mode "cluster" has more than one server, you will have to push the images to a registry or build the images in each server, so that when each of the servers in your cluster tries to start the containers it can get the Docker images for them, pulling them from a Docker Registry or because it has them already built locally.

If you are using a registry and pushing your images, you can omit running the previous script and instead using this one, in a single shot.

* Set these environment variables:
  * `TAG=prod`
  * `FRONTEND_ENV=production`
* Use the provided `scripts/build-push.sh` file with those environment variables:

```bash
TAG=prod FRONTEND_ENV=production bash ./scripts/build-push.sh
```

3. **Deploy your stack**

* Set these environment variables:
  * `DOMAIN=example.com`
  * `TRAEFIK_TAG=example.com`
  * `STACK_NAME=example.com`
  * `TAG=prod`
* Use the provided `scripts/deploy.sh` file with those environment variables:

```bash
DOMAIN=example.com \
TRAEFIK_TAG=example.com \
STACK_NAME=example.com \
TAG=prod \
bash ./scripts/deploy.sh
```

---

If you change your mind and, for example, want to deploy everything to a different domain, you only have to change the `DOMAIN` environment variable in the previous commands. If you wanted to add a different version / environment of your stack, like "`preproduction`", you would only have to set `TAG=preproduction` in your command and update these other environment variables accordingly. And it would all work, that way you could have different environments and deployments of the same app in the same cluster.

#### Deployment Technical Details

Building and pushing is done with the `docker-compose.yml` file, using the `docker-compose` command. The file `docker-compose.yml` uses the file `.env` with default environment variables. And the scripts set some additional environment variables as well.

The deployment requires using `docker stack` instead of `docker-swarm`, and it can't read environment variables or `.env` files. Because of that, the `deploy.sh` script generates a file `docker-stack.yml` with the configurations from `docker-compose.yml` and injecting the environment variables in it. And then uses it to deploy the stack.

You can do the process by hand based on those same scripts if you wanted. The general structure is like this:

```bash
# Use the environment variables passed to this script, as TAG and FRONTEND_ENV
# And re-create those variables as environment variables for the next command
TAG=${TAG?Variable not set} \
# Set the environment variable FRONTEND_ENV to the same value passed to this script with
# a default value of "production" if nothing else was passed
FRONTEND_ENV=${FRONTEND_ENV-production?Variable not set} \
# The actual comand that does the work: docker-compose
docker-compose \
# Pass the file that should be used, setting explicitly docker-compose.yml avoids the
# default of also using docker-compose.override.yml
-f docker-compose.yml \
# Use the docker-compose sub command named "config", it just uses the docker-compose.yml
# file passed to it and prints their combined contents
# Put those contents in a file "docker-stack.yml", with ">"
config > docker-stack.yml

# The previous only generated a docker-stack.yml file,
# but didn't do anything with it yet

# docker-auto-labels makes sure the labels used for constraints exist in the cluster
docker-auto-labels docker-stack.yml

# Now this command uses that same file to deploy it
docker stack deploy -c docker-stack.yml --with-registry-auth "${STACK_NAME?Variable not set}"
```

### Continuous Integration / Continuous Delivery

If you use GitLab CI, the included `.gitlab-ci.yml` can automatically deploy it. You may need to update it according to your GitLab configurations.

If you use any other CI / CD provider, you can base your deployment from that `.gitlab-ci.yml` file, as all the actual script steps are performed in `bash` scripts that you can easily re-use.

GitLab CI is configured assuming 2 environments following GitLab flow:

* `prod` (production) from the `production` branch.
* `stag` (staging) from the `master` branch.

If you need to add more environments, for example, you could imagine using a client-approved `preprod` branch, you can just copy the configurations in `.gitlab-ci.yml` for `stag` and rename the corresponding variables. The Docker Compose file and environment variables are configured to support as many environments as you need, so that you only need to modify `.gitlab-ci.yml` (or whichever CI system configuration you are using).

## Docker Compose files and env vars

There is a main `docker-compose.yml` file with all the configurations that apply to the whole stack, it is used automatically by `docker-compose`.

And there's also a `docker-compose.override.yml` with overrides for development, for example to mount the source code as a volume. It is used automatically by `docker-compose` to apply overrides on top of `docker-compose.yml`.

These Docker Compose files use the `.env` file containing configurations to be injected as environment variables in the containers.

They also use some additional configurations taken from environment variables set in the scripts before calling the `docker-compose` command.

It is all designed to support several "stages", like development, building, testing, and deployment. Also, allowing the deployment to different environments like staging and production (and you can add more environments very easily).

They are designed to have the minimum repetition of code and configurations, so that if you need to change something, you have to change it in the minimum amount of places. That's why files use environment variables that get auto-expanded. That way, if for example, you want to use a different domain, you can call the `docker-compose` command with a different `DOMAIN` environment variable instead of having to change the domain in several places inside the Docker Compose files.

Also, if you want to have another deployment environment, say `preprod`, you just have to change environment variables, but you can keep using the same Docker Compose files.

### The .env file

The `.env` file is the one that contains all your configurations, generated keys and passwords, etc.

Depending on your workflow, you could want to exclude it from Git, for example if your project is public. In that case, you would have to make sure to set up a way for your CI tools to obtain it while building or deploying your project.

One way to do it could be to add each environment variable to your CI/CD system, and updating the `docker-compose.yml` file to read that specific env var instead of reading the `.env` file.

## URLs

These are the URLs that will be used and generated by the project.

### Production URLs

Production URLs, from the branch `production`.

Backend: https://example.com/api/

Automatic Interactive Docs (Swagger UI): https://example.com/docs

Automatic Alternative Docs (ReDoc): https://example.com/redoc

### Development URLs

Development URLs, for local development.

Frontend: http://localhost

Backend: http://localhost/api/

Automatic Interactive Docs (Swagger UI): https://localhost/docs

Automatic Alternative Docs (ReDoc): https://localhost/redoc

PGAdmin: http://localhost:5050

Flower: http://localhost:5555

Traefik UI: http://localhost:8090

