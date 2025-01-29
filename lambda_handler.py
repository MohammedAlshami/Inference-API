from app import app
import awsgi

def lambda_handler(event, context):
    # Handle OPTIONS preflight request
    if event['requestContext']['http']['method'] == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            }
        }

    event['httpMethod'] = event['requestContext']['http']['method']
    event['path'] = event['requestContext']['http']['path']
    event['queryStringParameters'] = event.get('queryStringParameters', {})

    response = awsgi.response(app, event, context)

    # Ensure all responses include unrestricted CORS headers
    response.setdefault('headers', {})
    response['headers'].update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Methods': '*'
    })

    return response
