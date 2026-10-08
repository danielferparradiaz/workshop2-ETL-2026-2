FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir streamlit==1.44.1 pandas==2.2.3 SQLAlchemy==2.0.43 psycopg2-binary==2.9.10 plotly==6.0.1
COPY dashboard/app.py /app/app.py
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]
