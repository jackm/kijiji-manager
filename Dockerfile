FROM tiangolo/meinheld-gunicorn-flask:python3.6

# Not using prestart script; silence log output the sample script generates
RUN rm /app/prestart.sh

COPY kijiji_manager /app/kijiji_manager

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Module containing Flask app variable
ENV MODULE_NAME=kijiji_manager.__main__
