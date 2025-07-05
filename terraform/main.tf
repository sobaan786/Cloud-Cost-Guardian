# This file tells Terraform what to create in AWS

# Configure the AWS Provider
provider "aws" {
  region = "us-east-1"  # Same region from your setup
}

# Create an IAM role for our Lambda function
# (IAM = Identity and Access Management - it controls permissions)
resource "aws_iam_role" "lambda_role" {
  name = "cost-guardian-lambda-role"

  # This policy says "Lambda service can use this role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda permissions to our role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Package our Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../lambdas/cost-collector"
  output_path = "../lambdas/cost-collector.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "cost_collector" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "cost-guardian-collector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.lambda_handler"  # filename.function_name
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 30  # seconds

  # Environment variables (we'll use these later)
  environment {
    variables = {
      PROJECT = "cost-guardian"
    }
  }
}

# Output the function name so we know it was created
output "lambda_function_name" {
  value = aws_lambda_function.cost_collector.function_name
  description = "Name of our Lambda function"
}