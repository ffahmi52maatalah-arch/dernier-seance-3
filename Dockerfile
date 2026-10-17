FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Ollama runs on the host machine, not inside the container
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=llama3.1

EXPOSE 7860
EXPOSE 8000

CMD ["./start.sh"]
