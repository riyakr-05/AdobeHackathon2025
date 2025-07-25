# Use a slim Python base image compatible with AMD64
# python:3.9-slim-bullseye is a common and relatively small base.
# --platform=linux/amd64 ensures it targets the required architecture for the hackathon.
FROM --platform=linux/amd64 python:3.9-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by unstructured for PDF processing.
# poppler-utils and tesseract-ocr are essential for PDFs.
# libmagic-dev is for file type detection.
# tesseract-ocr-eng for English language support (commonly needed for OCR).
# We remove apt lists after installation to keep the image size down.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy your requirements.txt first to leverage Docker's build cache.
# If requirements.txt doesn't change, Docker won't re-run pip install on subsequent builds.
COPY requirements.txt .

# Install Python dependencies listed in requirements.txt.
# --no-cache-dir helps keep the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python application code into the container
COPY process_pdfs.py .

# Define the command to run when the container starts.
# This command will automatically be executed by the Docker runtime.
# Your main.py script is designed to process files from /app/input
# and save results to /app/output as per hackathon requirements.
CMD ["python", "processes_pdfs.py"]