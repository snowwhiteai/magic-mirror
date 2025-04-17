FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
