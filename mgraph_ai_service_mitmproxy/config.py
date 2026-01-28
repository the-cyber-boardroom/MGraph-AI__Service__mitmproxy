from mgraph_ai_service_mitmproxy import package_name

SERVICE_NAME                             = package_name
FAST_API__TITLE                          = "MGraph AI Service mitmproxy"
FAST_API__DESCRIPTION                    = "Base template for MGraph-AI microservices"
LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS = ['httpx==0.28.1'                           ,
                                            'memory-fs==v0.40.0'                      ,
                                            'mgraph-ai-service-cache-client==v0.32.0' ,
                                            'mgraph-ai-service-cache==v0.14.0'        ,
                                            'mgraph-ai-service-html-graph==v1.8.0'    ,
                                            'mgraph-ai-service-html==v0.6.25'         ,
                                            'mgraph-ai-service-semantic-text=v0.7.0'  ,
                                            'mgraph-db==v1.18.0'                      ,
                                            'osbot-fast-api-serverless==v1.33.0'      ]


MITMPROXY__SERVICE__WEB_CONSOLE__PATH              = 'console'
MITMPROXY__SERVICE__WEB_CONSOLE__ROUTE__START_PAGE = 'index'
MITMPROXY__SERVICE__WEB_CONSOLE__MAJOR__VERSION    = "v0/v0.1"
MITMPROXY__SERVICE__WEB_CONSOLE__LATEST__VERSION   = "v0.1.1"

ROUTES_PATHS__MITMPROXY__SERVICE__CONSOLE          = [f'/{MITMPROXY__SERVICE__WEB_CONSOLE__PATH}']