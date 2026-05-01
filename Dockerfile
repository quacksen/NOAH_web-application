FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Cloud Run sets the PORT env var automatically; it's best to reference it
ENV PORT=8080

# Using shell form to ensure $PORT is expanded correctly
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
