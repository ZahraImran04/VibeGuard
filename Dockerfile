FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy from the vibeguard subfolder
COPY vibeguard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vibeguard/ .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
