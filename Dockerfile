FROM python:3.8

WORKDIR /rm_reporting
COPY . /rm_reporting
EXPOSE 8084
RUN pip3 install pipenv && pipenv install --deploy --system

ENTRYPOINT ["python3"]
CMD ["run.py"]
