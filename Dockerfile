# app/Dockerfile

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

ADD . /app

RUN pip install -r requirements.txt

# add a .env if the user doesn't bind a volume to it
RUN touch /app/.env.local

# add secrets to .env
ARG URI
ARG DATABASE_NAME

RUN echo "URI=${URI}" >> /app/.env && \
    echo "DATABASE_NAME=${DATABASE_NAME}" >> /app/.env

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]