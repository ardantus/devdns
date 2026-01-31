FROM alpine:3.19

RUN apk add --no-cache dnsmasq

EXPOSE 53/tcp 53/udp

ENTRYPOINT ["dnsmasq", "-k"]
