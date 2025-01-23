FROM python:3.8

# Set the working directory
WORKDIR /var/task

# Copy the function code and requirements
COPY app.py /var/task
COPY requirements.txt /var/task

# Install the function's dependencies
RUN pip3 install --no-cache-dir -r requirements.txt --target "/var/task/venv"

# Set the CMD to your handler
CMD [ "app.handler" ]
