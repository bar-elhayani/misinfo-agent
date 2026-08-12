FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY shared_utils.py .
COPY agent/ ./agent/
COPY prompts/ ./prompts/

# The agent connects to the MCP server over the network - no direct
# filesystem access to data/ needed here at all.

CMD ["python3", "agent/supervisor.py"]