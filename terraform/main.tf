provider "aws" {
  region = "ap-southeast-1"
}

resource "aws_ecr_repository" "flask_app_repo" {
  name = "flask-app"
}

resource "aws_lambda_function" "inference_main" {
  function_name = "inference-main"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.flask_app_repo.repository_url}:latest"
  role          = aws_iam_role.lambda_execution_role.arn
  timeout       = 15

  # Environment variables (optional, add if needed)
  environment {
    variables = {
      ENV_VAR_KEY = "ENV_VAR_VALUE"
    }
  }
}

resource "aws_iam_role" "lambda_execution_role" {
  name               = "lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_execution_attachment" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference_main.function_name
  principal     = "apigateway.amazonaws.com"
}

output "lambda_function_arn" {
  value = aws_lambda_function.inference_main.arn
}

output "lambda_function_url" {
  value = aws_lambda_function.inference_main.invoke_arn
}
