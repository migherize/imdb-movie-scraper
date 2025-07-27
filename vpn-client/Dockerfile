FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y openvpn curl iproute2 iputils-ping && \
    echo "nameserver 1.1.1.1" > /etc/resolv.conf && \
    rm -rf /var/lib/apt/lists/*

ENV OVPN_FILE=japon.ovpn

COPY ${OVPN_FILE} /vpn-client/${OVPN_FILE}
COPY auth.txt /vpn-client/auth.txt
COPY check_country.sh /usr/local/bin/check_country.sh

RUN chmod +x /usr/local/bin/check_country.sh

CMD ["sh", "-c", "openvpn --config /vpn-client/${OVPN_FILE} --auth-user-pass /vpn-client/auth.txt"]

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD /usr/local/bin/check_country.sh
