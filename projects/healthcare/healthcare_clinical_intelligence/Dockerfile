FROM apache/airflow:2.10.4-python3.12

USER root
COPY src /opt/hci/src
COPY sql /opt/hci/sql
COPY data/samples /opt/hci/data/samples
RUN chown -R airflow:root /opt/hci

USER airflow
RUN pip install --no-cache-dir "psycopg[binary]>=3.2"
ENV PYTHONPATH=/opt/hci/src
