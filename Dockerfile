# Use an official Python runtime as a parent image
FROM python:3.6

RUN apt-get update

RUN apt-get install -y vim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000
EXPOSE 80

# Define environment variable
ENV NAME "Red Runner"
ENV RED_RUNNERS "184594|185368"
#ENV PORT 5000
# Run app.py when the container launches
CMD ["python", "main.py"]
