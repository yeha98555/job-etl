FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

COPY . /app

WORKDIR /app

RUN pip install -r linkedin_scaper/requirements.txt
CMD ["python", "linkedin_scaper/main.py"]