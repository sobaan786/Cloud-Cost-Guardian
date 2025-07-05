# This file lets us test our Lambda function on our computer

from index import lambda_handler

# Create fake event and context (Lambda provides these in real life)
test_event = {}
test_context = {}

# Call our function
result = lambda_handler(test_event, test_context)

# Print the result nicely
print("Lambda returned:")
print(f"Status Code: {result['statusCode']}")
print(f"Body: {result['body']}")

# Let's see if it worked
if result['statusCode'] == 200:
    print("\n✅ Success! Your Lambda function works!")
else:
    print("\n❌ Something went wrong...")