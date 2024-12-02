#FROM python:3.12-bullseye
FROM python:3.12

#ENV PYTHONBUFFERED=1
ENV PYTHONUNBUFFERED=1
#ENV PYTHONDONTWRITEBYTECODE=1

#WORKDIR /django
WORKDIR /app

#COPY requirements.txt requirements.txt
COPY requirements.txt .

RUN #pip3 install -r requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY .. .

RUN python manage.py collectstatic --noinput
RUN #python manage.py collectstatic

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
#CMD python manage.py runserver  0.0.0.0:8000
#CMD gunicorn --bind=0.0.0.0:8080 libApp.wsgi