FROM alpine:3.19

RUN apk add --no-cache dnsmasq \
    && mkdir -p /var/log/dnsmasq

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 53/tcp 53/udp

ENTRYPOINT ["/entrypoint.sh"]
