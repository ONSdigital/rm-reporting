.PHONY: build test start

install:
	pipenv install --dev

lint:
	pipenv run flake8 --max-line-length=120 --max-complexity=10 .

test: lint
	pipenv run pytest --cov=rm_reporting --cov-report xml

start:
	pipenv run python run.py
