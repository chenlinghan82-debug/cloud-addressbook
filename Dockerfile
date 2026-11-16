FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py database.py ./
COPY templates ./templates
COPY static ./static
ENV DB_PATH=/app/data/contacts.db
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
