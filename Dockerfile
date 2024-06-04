# Use an official Python runtime based on Ubuntu as a parent image
FROM python:3.11-buster

# Set the working directory in the container to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn 

## THIS SHOULD BE MODIFIED TO [common] if some of the libraries cause issues
RUN pip install large-image[all] --find-links https://girder.github.io/large_image_wheels

## NEED TO DEVENTUALLY SEE IF I NEED ALL OF GIRDER_LARGE_IMAGE..
RUN pip install girder_large_image 

RUN pip install tifftools

# Add the current directory contents into the container at /app
ADD . /app


# Make port 80 available to the world outside this container
EXPOSE 80

# Run the command to start uvicorn
CMD ["uvicorn", "fastApiTileServer:app", "--host", "0.0.0.0", "--port", "80", "--reload"]