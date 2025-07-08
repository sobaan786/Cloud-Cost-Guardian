import json
import boto3
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def lambda_handler(event, context):
    """
    Cloud Cost Guardian - Automated cost collection and monitoring
    Triggered daily by EventBridge to collect and analyze AWS costs
    """
    
    try:
        logger.info("Starting automated cost collection...")
        
        # Initialize Cost Explorer client
        ce_client = boto3.client('ce')
        
        # Calculate date range (last 7 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"Collecting costs from {start_date} to {end_date}")
        
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': str(start_date),
                'End': str(end_date)
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        # Process the cost data
        cost_data = process_cost_data(response)
        
        # Log summary for CloudWatch
        logger.info(f"Cost collection completed. Total 7-day cost: ${cost_data['total_cost']}")
        logger.info(f"Average daily cost: ${cost_data['avg_daily_cost']}")
        logger.info(f"Active services: {len(cost_data['daily_breakdown'])}")
        
        # Check for any cost anomalies (basic threshold)
        anomalies = detect_basic_anomalies(cost_data)
        if anomalies:
            logger.warning(f"Cost anomalies detected: {anomalies}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost collection completed successfully',
                'timestamp': datetime.now().isoformat(),
                'execution_type': 'automated' if 'source' in event else 'manual',
                'cost_summary': cost_data,
                'anomalies': anomalies
            }, default=decimal_default)
        }
        
    except Exception as e:
        logger.error(f"Error in cost collection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Cost collection failed',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def process_cost_data(response):
    """Process and structure the cost data from Cost Explorer"""
    
    daily_costs = []
    total_cost = 0
    service_totals = {}
    
    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        daily_total = 0
        services = {}
        
        for group in result['Groups']:
            service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
            cost = float(group['Metrics']['BlendedCost']['Amount'])
            
            services[service_name] = cost
            daily_total += cost
            
            # Track service totals
            if service_name in service_totals:
                service_totals[service_name] += cost
            else:
                service_totals[service_name] = cost
        
        daily_costs.append({
            'date': date,
            'total_cost': round(daily_total, 4),
            'services': services
        })
        
        total_cost += daily_total
    
    return {
        'total_cost': round(total_cost, 4),
        'avg_daily_cost': round(total_cost / 7, 4),
        'daily_breakdown': daily_costs,
        'service_totals': service_totals
    }

def detect_basic_anomalies(cost_data):
    """Basic anomaly detection - will enhance in Phase 3"""
    
    anomalies = []
    avg_cost = cost_data['avg_daily_cost']
    
    # Simple threshold: flag if any daily cost is 50% above average
    threshold = avg_cost * 1.5
    
    for day in cost_data['daily_breakdown']:
        if day['total_cost'] > threshold and day['total_cost'] > 0.01:  # Ignore tiny amounts
            anomalies.append({
                'date': day['date'],
                'cost': day['total_cost'],
                'threshold': threshold,
                'type': 'daily_spike'
            })
    
    # Flag if total cost exceeds $1 (basic budget alert for Free Tier)
    if cost_data['total_cost'] > 1.0:
        anomalies.append({
            'type': 'budget_warning',
            'total_cost': cost_data['total_cost'],
            'message': 'Weekly costs exceed $1 - review Free Tier usage'
        })
    
    return anomalies

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")