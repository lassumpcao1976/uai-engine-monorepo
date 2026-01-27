FROM python:3.11-slim

WORKDIR /app

COPY apps/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/ .

RUN mkdir -p artifacts templates projects

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
