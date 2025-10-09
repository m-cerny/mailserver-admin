FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies (Docker CLI + bash + minimal tools)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      docker-cli \
 && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose NiceGUI default port
EXPOSE 8080

# Run the app
CMD ["python", "main.py"]

# FROM python:3.11-slim

# # Install Docker CLI and bash
# RUN apt-get update \
#  && apt-get install -y docker.io bash \
#  && rm -rf /var/lib/apt/lists/*

# # Create working directory
# WORKDIR /app

# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the rest of the app
# COPY . .

# # Expose NiceGUI's default port
# EXPOSE 8080

# # Start the app
# CMD ["python", "main.py"]
