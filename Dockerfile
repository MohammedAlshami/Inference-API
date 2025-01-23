FROM public.ecr.aws/lambda/python:3.8

# Install system dependencies for certain Python packages
RUN yum install -y gcc python3-dev

# Copy function code
COPY app.py /var/task

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "/var/runtime"

# Set the CMD to your handler
CMD [ "app.handler" ]
