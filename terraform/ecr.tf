# ECR repository
resource "aws_ecr_repository" "example" {
  name = "example"
  tags = {
    "project" = "blog-example"
  }
}

resource "null_resource" "ecr_image" {
  provisioner "local-exec" {
    command = <<EOT
      docker build -t example .
      aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin ${aws_ecr_repository.example.repository_url}
      docker tag example:latest ${aws_ecr_repository.example.repository_url}:latest
      docker push ${aws_ecr_repository.example.repository_url}:latest
    EOT
  }
  
  triggers = {
    python_file = md5(file("../app.py"))
    docker_file = md5(file("../Dockerfile"))
  }
}

data "aws_ecr_image" "lambda_image" {
  depends_on      = [null_resource.ecr_image]
  repository_name = aws_ecr_repository.example.name
  image_tag       = "latest"
}