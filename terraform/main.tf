# EventBridge rule to trigger Lambda daily at 9 AM EST
resource "aws_cloudwatch_event_rule" "daily_cost_check" {
  name                = "cost-guardian-daily-trigger"
  description         = "Trigger cost guardian Lambda daily at 9 AM EST"
  schedule_expression = "cron(0 14 * * ? *)"  # 9 AM EST = 14:00 UTC

  tags = {
    Project = "CloudCostGuardian"
    Purpose = "DailyCostMonitoring"
  }
}

# EventBridge target to invoke our Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_cost_check.name
  target_id = "CostGuardianLambdaTarget"
  arn       = aws_lambda_function.cost_collector.arn
}

# Permission for EventBridge to invoke our Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_cost_check.arn
}

# Enhanced Lambda function with timezone awareness
resource "aws_lambda_function" "cost_collector" {
  filename         = "cost_collector.zip"
  function_name    = "cost-guardian-collector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  
  # This ensures Terraform redeploys when the ZIP file changes
  source_code_hash = filebase64sha256("cost_collector.zip")
  
  # Add environment variables for configuration
  environment {
    variables = {
      TIMEZONE = "US/Eastern"
      LOG_LEVEL = "INFO"
    }
  }

  tags = {
    Project = "CloudCostGuardian"
    Purpose = "CostDataCollection"
  }
}

# IAM role for Lambda (keeping existing permissions and adding CloudWatch Logs)
resource "aws_iam_role" "lambda_role" {
  name = "cost-guardian-lambda-role"

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

  tags = {
    Project = "CloudCostGuardian"
  }
}

# Enhanced IAM policy with logging permissions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cost-guardian-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast", 
          "ce:GetDimensionValues"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Output the EventBridge rule ARN for reference
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for daily cost collection"
  value       = aws_cloudwatch_event_rule.daily_cost_check.arn
}

# Output the next execution time (approximate)
output "next_execution_info" {
  description = "Daily execution at 9 AM EST (14:00 UTC)"
  value       = "Lambda will execute daily at 9:00 AM Eastern Time"
}