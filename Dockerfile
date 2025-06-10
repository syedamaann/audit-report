# Use an official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv, a fast Python package installer
RUN pip install uv

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies using uv's system-wide installation, ideal for containers
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the application source code into the container
COPY src/ src/

# Set the default command to run when the container starts. This will execute the main pipeline.
CMD ["python", "-m", "src.email_audit.pipeline"] 