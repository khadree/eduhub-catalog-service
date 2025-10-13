.PHONY: help install run test lint format clean docker-build docker-up docker-down k8s-deploy k8s-delete

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run           - Run the application locally"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean up cache and temp files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker Compose services"
	@echo "  make docker-down   - Stop Docker Compose services"
	@echo "  make k8s-deploy    - Deploy to Kubernetes"
	@echo "  make k8s-delete    - Delete from Kubernetes"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app --cov-report=html

lint:
	flake8 app/

format:
	black app/
	isort app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker build -t eduhub/catalog-service:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f catalog-service

k8s-deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/postgres-deployment.yaml
	kubectl apply -f k8s/redis-deployment.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl apply -f k8s/ingress.yaml

k8s-delete:
	kubectl delete -f k8s/

k8s-status:
	kubectl get all -n eduhub

migration-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migration-upgrade:
	alembic upgrade head

migration-downgrade:
	alembic downgrade -1
