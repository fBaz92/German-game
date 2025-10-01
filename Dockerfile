# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_MODE=cli \
    PORT=8501

WORKDIR /app

# System deps (if needed for future extensions)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code
COPY . /app

# Expose Streamlit default port (used when APP_MODE=ui)
EXPOSE 8501

# Default command: run CLI; switch to UI by setting APP_MODE=ui
CMD ["bash", "-lc", "if [ \"$APP_MODE\" = \"ui\" ]; then streamlit run streamlit_app.py --server.port=${PORT} --server.address=0.0.0.0; else python main.py; fi"] 