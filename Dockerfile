FROM python:3.10 AS builder

RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pyproject.toml pdm.lock /app/
COPY cherino /app/cherino

WORKDIR /app
RUN pdm config python.use_venv false && pdm install --prod --no-lock --no-editable

FROM python:3.10

WORKDIR /app

ENV PYTHONPATH=/app/pkgs
COPY --from=builder /app/__pypackages__/3.10/lib /app/pkgs

CMD ["python", "-m", "cherino"]
