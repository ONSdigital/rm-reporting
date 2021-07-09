.PHONY: build test start

build:
	pipenv install --dev

lint:
	pipenv run flake8
	pipenv check
	pipenv run isort .
	pipenv run black --line-length 120 .

lint-check:
	pipenv run flake8
	pipenv check
	pipenv run isort --check-only .
	pipenv run black --line-length 120 --check .

test: lint-check
	pipenv run pytest --cov=rm_reporting

start:
	pipenv run python run.py
