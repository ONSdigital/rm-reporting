.PHONY: build test start

build:
	pipenv install --dev

lint:
	pipenv check -i 70612 -i 70624
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8

lint-check:
	pipenv check -i 70612 -i 70624
	pipenv run isort --check-only .
	pipenv run black --line-length 120 --check .
	pipenv run flake8

test:
	pipenv run pytest --cov=rm_reporting --cov-report term-missing

start:
	pipenv run python run.py