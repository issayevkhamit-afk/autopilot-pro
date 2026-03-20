FROM python:3.12-slim

WORKDIR /app

# System deps (fonts for PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy DejaVu fonts for reportlab
RUN mkdir -p /app/fonts && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/fonts/ && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf /app/fonts/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create upload directory
RUN mkdir -p /app/uploads/logos

EXPOSE $PORT

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
