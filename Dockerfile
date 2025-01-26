FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for OpenCV and other libraries
RUN yum install -y mesa-libGL && yum clean all

# Copy requirements first to leverage Docker cache
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy all Python files and models
COPY app.py InferencePipeline.py ${LAMBDA_TASK_ROOT}/
COPY models/ ${LAMBDA_TASK_ROOT}/models/

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]
