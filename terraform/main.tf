terraform {
  backend "s3" {
    bucket = "example-blog-state"
    key    = "blog/terraform.tfstate"
    region = "ap-southeast-1"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.41"
    }
  }
}

provider "aws" {
  region  = "ap-southeast-1"
  profile = "default"
}
