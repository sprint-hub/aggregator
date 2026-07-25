.PHONY: help install dev test docker-up docker-down docker-build clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make docker-up    - Start all services with Docker"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-build - Build Docker images"
	@echo "  make clean        - Clean temporary files"

install:
	pip install -r requirements.txt

dev:
	python run.py

test:
	pytest tests/ -v --cov=app --cov-report=html

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/