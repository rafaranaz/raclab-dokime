# python:3.13-slim, pinned by the digest of its index (ADR-0052)
FROM docker.io/library/python@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90
RUN pip install --no-cache-dir --no-deps pyyaml==6.0.3 pytest==9.2.0 pluggy==1.7.0 iniconfig==2.3.1 packaging==26.3 pygments==2.21.0 import-linter==2.16 grimp==3.19 click==8.5.1 rich==15.0.0 markdown-it-py==4.2.0 mdurl==0.1.2 uv-build==0.11.8
COPY . /dokime/build
RUN pip install --no-cache-dir --no-deps --no-build-isolation /dokime/build
ENV PYTHONPATH=/dokime/project/src PYTHONDONTWRITEBYTECODE=1
