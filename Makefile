.PHONY: build test start

build:
	pipenv install --dev

#remove -i 70612 when jinja2 is updated beyond v3.1.4
#remove -i 70624 and -i 72731 when flask-cors is updated beyond v5.0.0
lint:
	pipenv check -i 70612 -i 70624 -i 72731
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8

lint-check:
	pipenv check -i 70612 -i 70624 -i 72731
	pipenv run isort --check-only .
	pipenv run black --line-length 120 --check .
	pipenv run flake8

test: lint-check
	pipenv run pytest --cov=rm_reporting --cov-report term-missing

start:
	pipenv run python run.py
