
# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV SPOTIFY_CLIENT_ID=your_client_id
ENV SPOTIFY_CLIENT_SECRET=your_client_secret
ENV DB_HOST=localhost
ENV DB_USER=root
ENV DB_PASSWORD=
ENV DB_NAME=dbspotify

# Run databaseManipulation.py when the container launches
CMD ["python", "databaseManipulation.py"]
