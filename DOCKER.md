# Local Docker Setup

Start the Django app and MySQL 8 database:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up -d --build
```

The app is available at:

```text
http://127.0.0.1:8001
```

The MySQL database is available from the host at:

```text
127.0.0.1:3307
```

Container credentials:

```text
database: wings
username: root
password: root
```

Run Django commands inside the app container:

```bash
docker compose exec app python manage.py check
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

Stop the stack:

```bash
docker compose down
```

Remove the local database volume and start with an empty database:

```bash
docker compose down -v
```
