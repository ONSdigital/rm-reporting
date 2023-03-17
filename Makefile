.PHONY: build test start

build:
	pipenv install --dev

lint:
	pipenv check
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8

lint-check:
	pipenv check
	pipenv run isort --check-only .
	pipenv run black --line-length 120 --check .
	pipenv run flake8

test: lint-check
	#pipenv run pytest --cov=rm_reporting --cov-report term-missing

start:
	pipenv run python run.py
