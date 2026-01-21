from mgraph_ai_service_mitmproxy import package_name

SERVICE_NAME                             = package_name
FAST_API__TITLE                          = "MGraph AI Service mitmproxy"
FAST_API__DESCRIPTION                    = "Base template for MGraph-AI microservices"
LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS = ['mgraph_ai_service_cache_client==0.28.0' ,
                                            'osbot-fast-api-serverless==1.33.0'     ]