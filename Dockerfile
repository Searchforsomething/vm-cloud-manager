# Use an official Python runtime as a parent image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apk update && \
    apk add --no-cache gcc musl-dev linux-headers libffi-dev openssl-dev cargo

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Run main.py when the container launches
CMD ["python", "main.py"]
