#checkov:skip=CKV_DOCKER_2: HEALTHCHECK not required - AWS Lambda does not support HEALTHCHECK
#checkov:skip=CKV_DOCKER_3: USER not required - A non-root user is used by AWS Lambda
FROM public.ecr.aws/lambda/python:3.12@sha256:0a3d34a8310dc339ea7afeb64725df5685da2e6f335dc9287cbc0cddc4a159f2

LABEL org.opencontainers.image.vendor="Ministry of Justice" \
      org.opencontainers.image.authors="Analytical Platform (analytical-platform@digital.justice.gov.uk)" \
      org.opencontainers.image.title="Ingestion Notify" \
      org.opencontainers.image.description="Ingestion notify image for Analytical Platform" \
      org.opencontainers.image.url="https://github.com/ministryofjustice/analytical-platform"

COPY --chown=nobody:nobody --chmod=0755 src/var/task/ ${LAMBDA_TASK_ROOT}

RUN python -m pip install --no-cache-dir --upgrade pip==24.0 \
    && python -m pip install --no-cache-dir --requirement requirements.txt

CMD ["handler.handler"]
