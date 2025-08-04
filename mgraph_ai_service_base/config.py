from mgraph_ai_service_base import package_name

SERVICE_NAME                             = package_name
LAMBDA_NAME__SERVICE__BASE               = f'service__{SERVICE_NAME}'
LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS = ['osbot-fast-api-serverless']