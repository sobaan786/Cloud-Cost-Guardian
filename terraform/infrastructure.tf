terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Create IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "cloud-cost-guardian-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach policy to role
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cloud-cost-guardian-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create Lambda function
resource "aws_lambda_function" "cost_analyzer" {
  filename      = "lambda.zip"
  function_name = "cloud-cost-guardian"
  role         = aws_iam_role.lambda_role.arn
  handler      = "index.lambda_handler"
  runtime      = "python3.11"
  timeout      = 30
  memory_size   = 128

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  tags = {
    Project = "CloudCostGuardian"
    Owner   = "Sobaan"
  }
}

# Output the function name
output "function_name" {
  value = aws_lambda_function.cost_analyzer.function_name
}

output "function_arn" {
  value = aws_lambda_function.cost_analyzer.arn
}
