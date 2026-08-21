FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY standalone_bot.py .
COPY static_game.html* ./
RUN mkdir -p data
ENV DATABASE_PATH=/app/data/game.db
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080
CMD ["python", "standalone_bot.py"]
