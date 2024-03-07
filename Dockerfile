# Use the official Python 3.9 image as the base image
FROM python:3.9

WORKDIR /code

# Prevent Python from writing bytecode files and force unbuffered mode for better Docker logging
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the requirements.txt file to the working directory
COPY ./requirements.txt /code/requirements.txt

# Install build dependencies, including libraries and development tools
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application code to the working directory
COPY ./backend .

