# Use the official Python image from the Docker Hub
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install the dependencies specified in the requirements file
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY ./app ./app/

EXPOSE 8000

CMD ["uvicorn", "app.backend:app","--host","0.0.0.0", "--port", "8000"]

