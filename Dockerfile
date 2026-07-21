# Use a lightweight official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt /app/

# Install dependencies (without compiling C-extensions thanks to the mock hack)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into work directory
COPY . /app/

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start Uvicorn server to host the API wrapper
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
