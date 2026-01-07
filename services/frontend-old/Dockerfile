FROM python:3.10-slim

WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 1. Copy the Streamlit config specifically first
COPY .streamlit .streamlit

# 2. Copy the rest of the app
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]