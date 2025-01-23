provider "aws" {
  region = "ap-southeast-1"
}

resource "aws_ecr_repository" "lambda_repo" {
  name = "my-lambda-repo"
}

resource "aws_lambda_function" "my_lambda" {
  function_name     = "my-lambda-function"
  role              = aws_iam_role.lambda_exec.arn
  package_type      = "Image"
  image_uri         = "${aws_ecr_repository.lambda_repo.repository_url}:latest"

  # Environment variables (optional)
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
