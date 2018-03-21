# RM Reporting

## Overview
This is the RM Reporting micro-service.

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
make install
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
