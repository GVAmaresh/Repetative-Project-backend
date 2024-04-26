FROM python:3.9

WORKDIR /

# Copy requirements.txt and install dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

# Copy the rest of the application files
COPY . .

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
