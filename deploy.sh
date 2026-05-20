#!/bin/bash
# Deployment script for housing project
# Run this before deploying to production

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "✓ Deployment preparation complete!"
echo "Your project is ready for deployment."
