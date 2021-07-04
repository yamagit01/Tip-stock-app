# 公式からpython3.7 on alpine linuxイメージをpull
FROM python:3.7-alpine

# 作業ディレクトリを設定
WORKDIR /usr/src/app

# 環境変数を設定
# Pythonがpyc filesとdiscへ書き込むことを防ぐ
ENV PYTHONDONTWRITEBYTECODE 1
# Pythonが標準入出力をバッファリングすることを防ぐ
ENV PYTHONUNBUFFERED 1

# requirements.txtをコピー
COPY ./requirements.txt /usr/src/app/requirements.txt

# create static directory
ENV STATIC_DIR=/var/www/app
RUN mkdir -p $STATIC_DIR && \
    mkdir $STATIC_DIR/static && \
    mkdir $STATIC_DIR/media

# create log directory
RUN mkdir -p /var/log/app

# Install packages for project
RUN apk update \
    && apk add --no-cache --virtual build-deps gcc python3-dev musl-dev libffi-dev rust cargo \
    && apk add --no-cache postgresql-dev \
    && apk add --no-cache  jpeg-dev zlib-dev libjpeg \
    && pip install -U  cffi pip setuptools \
    && pip install -r requirements.txt \
    && apk del --purge build-deps

# entrypoint.shをコピー
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

# ホストのカレントディレクトリ（現在はappディレクトリ）を作業ディレクトリにコピー
COPY . /usr/src/app/

# entrypoint.shを実行
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0", "-w", "2", "config.wsgi:application"]
# CMD ["gunicorn", "-b", "0.0.0.0", "--keep-alive", "60", "config.wsgi:application", "--timeout", "60"]
