FROM python:3.6

RUN apt-get update && apt-get install -y build-essential curl gunicorn
RUN pip3 install pipenv==8.3.1

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "rm_reporting:app", "-w=4"]

