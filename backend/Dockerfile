FROM python:3.11-slim

WORKDIR /app

# install system deps (if any)
RUN apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# tell FastAPI to reload in dev (optional)
ENV PYTHONUNBUFFERED=1

# expose the port uvicorn will run on
EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
