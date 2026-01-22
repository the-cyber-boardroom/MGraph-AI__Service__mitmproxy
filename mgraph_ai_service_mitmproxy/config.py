from mgraph_ai_service_mitmproxy import package_name

SERVICE_NAME                             = package_name
FAST_API__TITLE                          = "MGraph AI Service mitmproxy"
FAST_API__DESCRIPTION                    = "Base template for MGraph-AI microservices"
LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS = ['httpx==0.28.1'                          ,
                                            'mgraph_ai_service_cache_client==0.28.0' ,
                                            'osbot-fast-api-serverless==1.33.0'     ]


MITMPROXY__SERVICE__WEB_CONSOLE__PATH              = 'console'
MITMPROXY__SERVICE__WEB_CONSOLE__ROUTE__START_PAGE = 'index'
MITMPROXY__SERVICE__WEB_CONSOLE__MAJOR__VERSION    = "v0/v0.1"
MITMPROXY__SERVICE__WEB_CONSOLE__LATEST__VERSION   = "v0.1.0"

ROUTES_PATHS__MITMPROXY__SERVICE__CONSOLE          = [f'/{MITMPROXY__SERVICE__WEB_CONSOLE__PATH}']