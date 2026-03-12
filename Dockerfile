# Use Python 3.12 slim image as the base for building dependencies
# NOTE: use slim version to reduce image size, which provides everything needed for uv and dependency installation
FROM python:3.12-slim AS builder

# Create the /app directory if it doesnt exist and set it as the current working directory
# NOTE: /app is a common convention for application code
WORKDIR /app

# Copy uv (fast Python package manager) from its official image into /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy only dependency files first (not the whole app)
# This allow dependency installation to re-run when dependencies actually change, which speeds up builds.
COPY pyproject.toml uv.lock ./

# Install dependencies into .venv using the lock file
# --frozen = use uv.lock exactly, don't update it
# --no-dev = skip dev dependencies (pytest, etc.) for smaller production image
RUN uv sync --frozen --no-dev

# The final image is built from the runtime stage, only contains what you copy into it from builder stage
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the virtual environment from the builder stage into the runtime stage
# NOTE: copy only .venv since runtime only requires installed packages, not uv or lock files
COPY --from=builder /app/.venv /app/.venv

# Adds the application code and other project files to the runtime image so the container can run the fastapi app
COPY . .

# Use the uvicorn from the venv and its installed packages
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]