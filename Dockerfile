FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt && useradd -u 10001 -m analyst
COPY --chown=analyst:analyst . .
RUN mkdir -p runtime && chown analyst:analyst runtime
USER analyst
EXPOSE 8000 8501
CMD ["python", "-m", "uvicorn", "bankops.api:app", "--host", "0.0.0.0", "--port", "8000"]
