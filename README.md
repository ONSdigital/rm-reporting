# RM Reporting

This is the RM Reporting micro-service.  It's used to get collate a number of stats from the various ras-rm services to
be used by things like the responses-dashboard, etc.

## Setup

Install pipenv

```bash
pip install pipenv
```

Use pipenv to create a virtualenv and install dependencies

```bash
pipenv install
```
you can also use the makefile to do this

```bash
make build
```

## Running

Use the makefile to run
```bash
make start
```

or run
```bash
pipenv run python3 run.py
```

To test the service is up:

```
curl http://localhost:8084/info
```

## Local testing

```bash
make test
```

force build
