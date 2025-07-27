FROM python:3.11 AS BUILDER

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.11-slim AS IMAGE
COPY --from=BUILDER /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app:$PYTHONPATH

WORKDIR /app
COPY ./app /app

# ENTRYPOINT ["tail", "-f", "/dev/null"]
CMD /opt/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
# CMD fastapi dev src/main.py --host 0.0.0.0 --port 8080