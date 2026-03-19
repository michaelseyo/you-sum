FROM python:3.12-slim

# Keep Python output container-friendly
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install app dependencies into a project-local virtualenv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Run all following commands from /app
WORKDIR /app

# Install uv for locked dependency installs
RUN pip install --no-cache-dir uv

# Copy dependency metadata first for better Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy the API source code into the image
COPY . .

# Document the port used by uvicorn
EXPOSE 8000

# Start the FastAPI app on the platform-provided port when available
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
