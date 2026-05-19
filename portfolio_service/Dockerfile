FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY portfolio_service/ ./portfolio_service/

ENV PYTHONPATH=/app

CMD ["uvicorn", "portfolio_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
