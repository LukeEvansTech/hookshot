FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/

USER 1000:1000

EXPOSE 8000

ENTRYPOINT ["python", "-m", "src.main"]
