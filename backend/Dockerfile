FROM python:3.11-slim

WORKDIR /app

# Unbuffered stdout/stderr so print()/logging output reaches `docker compose logs`
# immediately (otherwise Python block-buffers when stdout is a pipe).
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
