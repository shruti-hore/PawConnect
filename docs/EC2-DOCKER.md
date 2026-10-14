# Docker deployment on AWS EC2

This deployment runs the Flask API and the static frontend as separate
containers. Nginx serves the frontend and proxies `/api` requests to Flask.
Only Nginx is published on the EC2 host; the API listens on the private
Compose network. PostgreSQL remains an external service such as Amazon RDS.

## Configure the EC2 instance

1. Launch a Linux EC2 instance in the same VPC as the RDS database.
2. Install Docker Engine and the Docker Compose plugin for the instance's Linux
   distribution, then verify `docker --version` and `docker compose version`.
3. In the EC2 security group, allow inbound TCP port 80 from the intended
   clients. Restrict SSH (TCP 22) to your own IP. Do not expose port 5000.
4. Configure the RDS security group to allow PostgreSQL (TCP 5432) from the EC2
   security group, not from the public internet.

For HTTPS, terminate TLS at an Application Load Balancer or another maintained
TLS reverse proxy; do not send database or application credentials over an
untrusted network.

## Configure and start PawConnect

On the instance, clone the repository and move into its root directory. Create
the deployment environment file from the example:

```sh
cp .env.example .env
```

Edit `.env` with the RDS endpoint, database name, database username and
password, Cognito user-pool settings, and a unique random `SECRET_KEY`
(generate one with `openssl rand -hex 32`). Compose refuses to start if
`DATABASE_URL` or `SECRET_KEY` is empty. Keep `.env` out of source control.
The RDS security group must permit the connection from this instance. URL-encode
reserved characters in the database username and password. For production use,
prefer storing environment secrets in AWS Systems Manager Parameter Store or
Secrets Manager and injecting them at deployment time rather than committing
them to an image.

Build the images and apply the checked-in schema migrations before starting the
web containers:

```sh
docker compose build
docker compose run --rm backend flask --app "app:create_app()" db upgrade
docker compose up -d
```

The frontend will be available at `http://EC2_PUBLIC_DNS/` (or your configured
domain). The API health endpoint is `http://EC2_PUBLIC_DNS/api/health`.
Check container state and logs with:

```sh
docker compose ps
docker compose logs --tail=100
```

To deploy a code update, pull the new revision, rebuild, apply any pending
migrations, then recreate the services:

```sh
docker compose build
docker compose run --rm backend flask --app "app:create_app()" db upgrade
docker compose up -d
```

Back up the RDS database before applying migrations. The API container does not
automatically run migrations at startup, avoiding concurrent migration attempts
when multiple instances start.
