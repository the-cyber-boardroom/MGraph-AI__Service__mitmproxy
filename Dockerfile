# Container image for MGraph-AI Service mitmproxy
#
# The service is a standard ASGI app (see README) and registers all of its
# downstream services in-memory (run_in_memory = True), so the container is
# fully self-contained and needs no AWS Lambda layers to run.
#
# Build : docker build -t diniscruz/mgraph-ai-service-mitmproxy .
# Run   : docker run -p 10011:10011 \
#             -e FAST_API__AUTH__API_KEY__NAME=x-api-key \
#             -e FAST_API__AUTH__API_KEY__VALUE=dev-key \
#             diniscruz/mgraph-ai-service-mitmproxy

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10011

WORKDIR /app

# git is required for any VCS-based pip installs in the dependency tree
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# install the service (deps come from pyproject) plus the uvicorn ASGI server
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -e . \
    && pip install --no-cache-dir uvicorn

EXPOSE 10011

CMD ["sh", "-c", "uvicorn mgraph_ai_service_mitmproxy.fast_api.lambda_handler:app --host 0.0.0.0 --port ${PORT:-10011}"]
