# Use an official Python image
FROM python:3.10

# Set working directory (this will be the root of your repo)
WORKDIR /newdynamicapk

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (including bot.py, etc.)
COPY . .

# Run your Flask app
CMD ["python", "bot.py"]
