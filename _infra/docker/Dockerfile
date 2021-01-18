FROM python:3.9

RUN apt-get update && apt-get install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

CMD ["gunicorn", "-b", "0.0.0.0:8080", "rm_reporting:app", "-w=4"]

