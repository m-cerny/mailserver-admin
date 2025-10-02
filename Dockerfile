FROM python:3.11-slim

# Install Docker CLI and bash
RUN apt-get update \
 && apt-get install -y docker.io bash \
 && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose NiceGUI's default port
EXPOSE 8080

# Start the app
CMD ["python", "main.py"]
