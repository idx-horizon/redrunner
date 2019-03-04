# Use an official Python runtime as a parent image
FROM python:3.6

RUN apt-get update

RUN apt-get install -y vim

# Set the working directory to /redrunner
WORKDIR /redrunner

# Copy the current directory contents into the container at /app
COPY . /redrunner

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000
EXPOSE 80

# Define environment variable
ENV RR_NAME "Red Runner"
ENV RR_PUBLIC_FLAG "1"
ENV RR_PORT 8888

# Run main.py when the container launches
CMD ["python", "main.py"]
