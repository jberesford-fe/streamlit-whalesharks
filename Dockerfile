# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies required for Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files (if available)
COPY pyproject.toml poetry.lock* /app/

# Install dependencies using Poetry
# The --no-root option tells Poetry to not install the root package (your package)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the .streamlit directory and the secrets.toml file
COPY .streamlit/ /app/.streamlit/

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
