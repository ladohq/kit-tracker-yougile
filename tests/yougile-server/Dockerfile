# Yougile's self-hosted server (Linux x64 only), for trying the kit on a real Yougile.
# The distribution is not committed: download it next to this file first (README.md).
FROM --platform=linux/amd64 debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY yougile.tar.gz /tmp/yougile.tar.gz
RUN tar xf /tmp/yougile.tar.gz -C /opt && rm /tmp/yougile.tar.gz
WORKDIR /opt/yougile
EXPOSE 8001
CMD ["./server"]
