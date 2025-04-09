FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install uv
RUN uv pip install --no-cache -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
