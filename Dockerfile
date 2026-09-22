# 1. Use an official, lightweight Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy just the requirements files first (helps with faster Docker builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# 4. Copy your application files into the container
COPY . .

# 5. Inform Docker that the container listens on port 8000 at runtime
EXPOSE 8000

# 6. Run uvicorn when the container launches
# We bind to 0.0.0.0 so external devices (like your phone) can connect
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
