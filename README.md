# RM Reporting
[![Build Status](https://travis-ci.org/ONSdigital/rm-reporting.svg?branch=main)](https://travis-ci.org/ONSdigital/rm-reporting)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d95caec803dd43e292e468bb910db9d5)](https://www.codacy.com/app/tej99/rm-reporting?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/rm-reporting&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/ONSdigital/rm-reporting/branch/main/graph/badge.svg)](https://codecov.io/gh/ONSdigital/rm-reporting)

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
