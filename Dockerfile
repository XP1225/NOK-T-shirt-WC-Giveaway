# Base image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Define the environment variable for Flask
ENV FLASK_APP=app.py  # Replace 'app.py' with your main Flask file name if it's different

# Expose the port that the app runs on
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
