.PHONY: build test start

build:
	pipenv install --dev

lint:
	pipenv check -i 51499
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8

lint-check:
	pipenv check -i 51499
	pipenv run isort --check-only .
	pipenv run black --line-length 120 --check .
	pipenv run flake8

test: lint-check
	pipenv run pytest --cov=rm_reporting

start:
	pipenv run python run.py
