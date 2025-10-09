# Mailserver Admin

A web-based administration interface for managing user accounts on [docker-mailserver](https://github.com/docker-mailserver/docker-mailserver).

You can try a demo of the app:: 
- [demo web site](https://demo-mail.redandblack.cz)
- username: demouser@demo.demo
- password: demouser

## Features

- **User Management**: Add, update, and delete mail users.
- **Aliases Management**: View and manage user aliases.
- **Quota Monitoring**: Check mailbox usage and quotas.
- **Web Interface**: Easy-to-use UI for daily administration tasks.

## Requirements

- Docker
- A running `docker-mailserver` instance

## Quick Start with Docker Compose

You can run `docker-mailserver` together with `mailserver-admin` using `docker-compose`.  
Here is an example `docker-compose.yml` setup:

```yaml
version: "3.8"

services:
  mailserver:
    image: ghcr.io/docker-mailserver/docker-mailserver:latest
    container_name: mailserver
    hostname: ###
    ports:
      - "25:25"
      - "143:143"
      - "465:465"
      - "587:587"
      - "993:993"
      - "11334:11334"
    volumes:
      - ./dms/docker-data/dms/mail-data/:/var/mail/
      - ./dms/docker-data/dms/mail-state/:/var/mail-state/
      - ./dms/docker-data/dms/mail-logs/:/var/log/mail/
      - ./dms/docker-data/dms/config/:/tmp/docker-mailserver/
      - /etc/localtime:/etc/localtime:ro
      - /etc/letsencrypt:/etc/letsencrypt
    restart: always
    stop_grace_period: 1m
    healthcheck:
      test: "ss --listening --tcp | grep -P 'LISTEN.+:smtp' || exit 1"
      timeout: 3s
      retries: 0
    environment:
      - SSL_TYPE=letsencrypt

  reverse-proxy:
    image: nginx:latest
    container_name: reverse-proxy
    volumes:
      - ./reverse-proxy/nginx/conf.d:/etc/nginx/conf.d
    ports:
      - "80:80"
      - "443:443"
    restart: always
    networks:
      - mailnet

  mailserver-admin:
    build: mailserver-admin
    container_name: mailserver-admin
    environment:
      - CONT_NAME=mailserver
      - ADMINS=admin_1@mail.addres, admin_2@mail.addres
      - SITE_TITLE=Your title
    volumes:
      - ./mailserver-admin:/app
      - /var/run/docker.sock:/var/run/docker.sock
      - ./dms/docker-data/dms/config/:/app/mailserver:ro
    stdin_open: true
    tty: true
    networks:
      - mailnet

networks:
  mailnet:
