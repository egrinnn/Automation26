FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN chmod +x docker-entrypoint.sh

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
