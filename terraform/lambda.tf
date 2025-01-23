resource "aws_lambda_function" "example" {
  depends_on    = [null_resource.ecr_image]
  function_name = "example-lambda"
  architectures = ["arm64"]
  role          = aws_iam_role.lambda.arn
  timeout       = 180
  memory_size   = 10240
  image_uri     = "${aws_ecr_repository.example.repository_url}:latest"
  package_type  = "Image"
}

resource "aws_cloudwatch_log_group" "example_service" {
  name              = "/aws/lambda/example_service"
  retention_in_days = 14
}
