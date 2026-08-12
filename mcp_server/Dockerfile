FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching - only reinstalls if
# requirements.txt changes, not on every code change)
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy the code this service actually needs: the server itself, the
# shared utilities, and the prompts it reads from disk at startup
COPY shared_utils.py .
COPY mcp_server/ ./mcp_server/
COPY prompts/ ./prompts/

# data/ (DuckDB file + Chroma store) is mounted as a volume at runtime,
# not baked into the image - it's large and changes independently of code

EXPOSE 8000

CMD ["python3", "mcp_server/server.py"]