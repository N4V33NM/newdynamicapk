# Use slim Python image
FROM python:3.10-slim

# Install pip dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose the port Flask uses
EXPOSE 5000

# Start the Flask bot
CMD ["python", "bot.py"]
