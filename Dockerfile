# Use an official Python runtime as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy the contents of your repo to the container
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the port Flask/Gunicorn will run on
EXPOSE 5000

# Run the app using gunicorn
CMD ["gunicorn", "bot:app", "--bind", "0.0.0.0:5000"]
