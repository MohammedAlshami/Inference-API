# ECR repository
resource "aws_ecr_repository" "example" {
  name = "example"
  tags = {
    "project" = "blog-example"
  }
}

resource "null_resource" "ecr_image" {
  triggers = {
    python_file = md5(file("../app.py"))
    docker_file = md5(file("../Dockerfile"))
  }
}

data "aws_ecr_image" "lambda_image" {
  depends_on     = [null_resource.ecr_image]
  repository_name = aws_ecr_repository.example.name
  image_tag       = "latest"
}
