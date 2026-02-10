#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for database to be ready (optional, useful for init containers)
if [ "$WAIT_FOR_DB" = "true" ]; then
    echo "Waiting for database..."
    python << END
import sys
import time
import psycopg2
from decouple import config

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        # Try to import the database credentials
        if config('USE_AWS_SECRETS', default='False').strip().lower() in ['true', '1', 'yes', 'on']:
            from config.utils.aws_secrets import get_rds_credentials
            db_config = get_rds_credentials()
            conn = psycopg2.connect(
                dbname=db_config['NAME'],
                user=db_config['USER'],
                password=db_config['PASSWORD'],
                host=db_config['HOST'],
                port=db_config['PORT']
            )
        else:
            conn = psycopg2.connect(
                dbname=config('DB_NAME'),
                user=config('DB_USER'),
                password=config('DB_PASSWORD'),
                host=config('DB_HOST'),
                port=config('DB_PORT')
            )
        conn.close()
        print("Database is ready!")
        break
    except Exception as e:
        retry_count += 1
        print(f"Database not ready (attempt {retry_count}/{max_retries}): {e}")
        time.sleep(2)

if retry_count >= max_retries:
    print("Failed to connect to database after maximum retries")
    sys.exit(1)
END
fi

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

# Collect static files
if [ "$COLLECT_STATIC" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Create superuser if needed (for initial setup)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser if not exists..."
    python manage.py shell << END
from accounts.models import User
if not User.objects.filter(email='${DJANGO_SUPERUSER_EMAIL}').exists():
    User.objects.create_superuser(
        email='${DJANGO_SUPERUSER_EMAIL}',
        username='${DJANGO_SUPERUSER_USERNAME}',
        password='${DJANGO_SUPERUSER_PASSWORD}'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
fi

echo "Starting Gunicorn server..."
exec "$@"
