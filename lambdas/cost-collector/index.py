import json
import boto3
from datetime import datetime, timedelta

def handler(event, context):
    """
    Lambda function to collect AWS cost data
    """
    # Create Cost Explorer client
    ce_client = boto3.client('ce')
    
    # Get dates for the last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    try:
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        # Process the results
        daily_costs = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_cost = 0
            services = {}
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                services[service] = round(cost, 2)
                total_cost += cost
            
            daily_costs.append({
                'date': date,
                'total_cost': round(total_cost, 2),
                'services': services
            })
        
        # Calculate average daily cost
        total = sum(day['total_cost'] for day in daily_costs)
        avg_daily_cost = round(total / len(daily_costs), 2) if daily_costs else 0
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost data collected successfully',
                'summary': {
                    'period': f'{start_date} to {end_date}',
                    'total_cost': round(total, 2),
                    'average_daily_cost': avg_daily_cost,
                    'days_analyzed': len(daily_costs)
                },
                'daily_costs': daily_costs
            })
        }
        
    except Exception as e:
        print(f"Error fetching cost data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to fetch cost data',
                'details': str(e)
            })
        }