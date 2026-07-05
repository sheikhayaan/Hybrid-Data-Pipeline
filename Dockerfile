FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN g++ -O2 data_engine.cpp -o data_engine \
    && ./data_engine 1000 \
    && python model_pipeline.py

EXPOSE 8501

CMD streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8501} --server.headless true
