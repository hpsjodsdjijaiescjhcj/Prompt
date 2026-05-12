FROM python:3.12-slim

WORKDIR /app/backend

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 5001
CMD ["python", "app.py"]
