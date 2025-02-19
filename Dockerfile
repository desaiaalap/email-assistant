FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the Python script
COPY download_dataset.py /app/

# Install required dependencies if any
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Define the default command
CMD ["python", "download_dataset.py"]
