FROM python:3.10-slim

WORKDIR /app

# Copy requirements first, install, THEN copy the rest of the code.
# This ordering matters for Docker's build cache: dependencies change
# far less often than your actual code, so if only code changes,
# Docker reuses the cached "pip install" layer instead of re-running it --
# meaningfully faster rebuilds during development.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
