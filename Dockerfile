FROM public.ecr.aws/lambda/python:3.8
RUN pip install requests pandas beautifulsoup4 lxml
COPY my_lambda_function.py ./
CMD ["my_lambda_function.lambda_handler"]