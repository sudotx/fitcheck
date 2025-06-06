.PHONY: run migrate-up migrate-down migrate-create

# Run the application with Gunicorn
run:
	gunicorn -c gunicorn.conf.py wsgi:app

# Database migration commands
migrate-up:
	flask db upgrade

migrate-down:
	flask db downgrade

# Development server
dev:
	flask run --debug

# Install dependencies
install:
	pip install -r requirements.txt

# Create a new migration
# Usage: make migrate-create message="your migration message"
migrate-create:
	flask db migrate -m "$(message)"

# Show migration history
migrate-history:
	flask db history

# Show current migration version
migrate-current:
	flask db current

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} + 