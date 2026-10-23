FROM golang:1.21-bookworm AS builder

RUN git clone --depth 1 --branch RELEASE.2024-01-28T22-35-53Z https://github.com/minio/minio.git /src/minio
WORKDIR /src/minio
RUN CGO_ENABLED=0 go build -trimpath -o /out/minio .

RUN git clone --depth 1 --branch RELEASE.2024-01-28T16-23-14Z https://github.com/minio/mc.git /src/mc
WORKDIR /src/mc
RUN CGO_ENABLED=0 go build -trimpath -o /out/mc .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/minio /usr/bin/minio
COPY --from=builder /out/mc /usr/bin/mc

EXPOSE 9000 9001
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--console-address", ":9001"]
