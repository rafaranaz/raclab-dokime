# python:3.13-slim, pinned by the digest of its index (ADR-0052)
FROM docker.io/library/python@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90
RUN pip install --no-cache-dir --no-deps pytest==8.3.4 pluggy==1.7.0 iniconfig==2.3.1 packaging==26.3 pytest-cov==6.0.0 coverage==7.17.3
ENV PYTHONDONTWRITEBYTECODE=1 COVERAGE_FILE=/tmp/.coverage
