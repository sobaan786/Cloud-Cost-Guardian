import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """Check AWS costs for the last 7 days"""
    
    # Connect to AWS Cost Explorer
    ce = boto3.client('ce', region_name='us-east-1')
    
    # Get dates
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    try:
        # Get cost data from AWS
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': str(week_ago),
                'End': str(today)
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        # Add up all the costs
        total = 0
        days_analyzed = 0
        for day in response['ResultsByTime']:
            cost = float(day['Total']['UnblendedCost']['Amount'])
            total += cost
            days_analyzed += 1
        
        # Create response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost analysis successful!',
                'period': '7 days',
                'total_cost': round(total, 2),
                'daily_average': round(total / 7, 2),
                'days_analyzed': days_analyzed,
                'analysis_date': str(datetime.now())
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to analyze costs'
            })
        }