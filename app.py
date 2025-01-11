name: Build and Deploy to Lambda

on:
  push:
    branches:
      - main  # Trigger on pushes to the main branch

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    # Checkout code
    - name: Checkout code
      uses: actions/checkout@v3

    # Set up Python 3.11 (for local testing, if needed)
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11

    # Install dependencies (optional if you want to test locally)
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    # Log in to Amazon ECR
    - name: Log in to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    # Build the Docker image
    - name: Build Docker image
      run: |
        aws_region="ap-southeast-1"  # Updated with your region
        ecr_repo="your-ecr-repository-name"  # Update with your ECR repo name
        image_tag="latest"

        # Build the Docker image
        docker build -t $ecr_repo:$image_tag .

        # Tag the Docker image for ECR
        aws_account_id=$(aws sts get-caller-identity --query Account --output text)
        docker tag $ecr_repo:$image_tag $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/$ecr_repo:$image_tag

    # Push the Docker image to ECR
    - name: Push Docker image to ECR
      run: |
        docker push $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/$ecr_repo:$image_tag

    # Deploy to AWS Lambda
    - name: Deploy to AWS Lambda
      run: |
        aws_region="ap-southeast-1"  # Updated with your region
        lambda_function_name="your-lambda-function-name"  # Update with your Lambda function name

        # Update the Lambda function to use the new container image
        aws lambda update-function-code \
          --function-name $lambda_function_name \
          --image-uri $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/$ecr_repo:$image_tag
