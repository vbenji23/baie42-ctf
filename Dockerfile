# Image du lab vulnerable Baie 42 (entrainement uniquement)
FROM python:3.12-slim

# Bonnes pratiques : utilisateur non-root, pas de cache pip
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd -m appuser
USER appuser

EXPOSE 5000
ENV HOST=0.0.0.0 PORT=5000
CMD ["python", "app.py"]
