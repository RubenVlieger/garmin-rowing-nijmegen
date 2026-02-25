# Use a slim Python 3.11 image
FROM python:3.11-slim-bookworm

# Install Astral UV (blazing fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependencies first for caching
COPY backend/requirements.txt ./backend/

# Install dependencies via UV system-wide
RUN uv pip install --system -r backend/requirements.txt

# Copy the rest of the application
COPY . .

# Expose the Flask port (used in docker-compose)
EXPOSE 8001

# The default command will be overridden by docker-compose for the scheduler vs the web server.
# By default, run the web server.
CMD ["gunicorn", "-b", "0.0.0.0:8001", "-w", "2", "--chdir", "backend", "analytics_server:app"]
