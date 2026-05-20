#!/bin/bash
# Pre-deployment validation script
# Run this before deploying to production

echo "🔍 Starting Pre-Deployment Validation..."
echo ""

# Check migrations
echo "✓ Checking migrations..."
python manage.py migrate --check

# Run tests
echo "✓ Running tests..."
python manage.py test listings

# Collect static files
echo "✓ Collecting static files..."
python manage.py collectstatic --noinput

# Check deployment readiness
echo "✓ Running deployment checks..."
python manage.py check --deploy

echo ""
echo "✅ All pre-deployment checks passed!"
echo ""
echo "Next steps:"
echo "1. Update .env with production values"
echo "2. Set DEBUG=False in your .env"
echo "3. Generate a new SECRET_KEY"
echo "4. Update ALLOWED_HOSTS with your domain"
echo "5. Deploy to your hosting provider"
