FROM python:3.11 AS builder

RUN pip install -U pip setuptools wheel
RUN pip install pdm
RUN mkdir -p /app/__pypackages__

WORKDIR /app

COPY pyproject.toml pdm.lock /app/
RUN pdm sync --prod --no-editable

COPY cherino /app/cherino
RUN pdm sync --prod --no-editable

FROM python:3.11-slim

WORKDIR /app

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo "Asia/Shanghai" > /etc/timezone

ENV PYTHONPATH=/app/pkgs
COPY --from=builder /app/__pypackages__/3.11/lib /app/pkgs

CMD ["python", "-m", "cherino"]
