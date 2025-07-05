import json
import datetime

def lambda_handler(event, context):
    """
    This functions runs when lambda is triggered 
    - event: contains data sent to our function 
    - context: contains info about the execution enviroment 
    """ 
    # Let's create a simple response
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    response = {
        "statusCode": 200,  # 200 means "success" in HTTP
        "body": json.dumps({
            "message": "Hello from your Cost Guardian!",
            "timestamp": current_time,
            "status": "Lambda is working!"
        })
    }
    
    # Print to CloudWatch Logs (so we can see it ran)
    print(f"Function executed at: {current_time}")
    
    return response