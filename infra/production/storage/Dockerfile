# Keep the existing server version for data migration. Fetch only official,
# checksum-verified releases: the old Docker registry tag is no longer pullable.
FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS binaries
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /artifacts
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) server_sha=b0638a7f484c53c2d22777f9d8d777d600a321aaeff526bf42a8524c89bfec5e; \
             client_sha=fc195c3ad5c19b91d96bbb42d79af94173aa491ebcda9ca372c4f382546135ec ;; \
      arm64) server_sha=7c22acede0af52d9044f9ac67bde5641d4f9c54930e80c09216634a6603a92d7; \
             client_sha=683aebeef6f8e0d18fcfec152e8e8d0f7e7e8fa5859b5ea2bd2414280b7398c6 ;; \
      *) echo 'Unsupported storage architecture' >&2; exit 1 ;; \
    esac; \
    curl --fail --location --retry 3 --connect-timeout 20 --max-time 600 \
      "https://github.com/minio/minio/releases/download/RELEASE.2024-01-28T22-35-53Z/minio.linux-${TARGETARCH}.RELEASE.2024-01-28T22-35-53Z" -o minio; \
    curl --fail --location --retry 3 --connect-timeout 20 --max-time 600 \
      "https://github.com/minio/mc/releases/download/RELEASE.2024-01-28T16-23-14Z/mc.linux-${TARGETARCH}.RELEASE.2024-01-28T16-23-14Z" -o mc; \
    printf '%s  minio\n%s  mc\n' "$server_sha" "$client_sha" | sha256sum --check --strict; \
    chmod 755 minio mc; \
    curl --fail --location --retry 3 --max-time 60 \
      https://raw.githubusercontent.com/minio/minio/7743d952dc16ccab26ca9240855089535e548062/LICENSE -o MINIO-LICENSE; \
    curl --fail --location --retry 3 --max-time 60 \
      https://raw.githubusercontent.com/minio/mc/ba9fc6a3075df6d8a413cc7e423645706aaefae1/LICENSE -o MC-LICENSE

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 mathvision \
    && useradd --uid 10001 --gid 10001 --create-home mathvision \
    && mkdir /data && chown mathvision:mathvision /data
COPY --from=binaries /artifacts/minio /artifacts/mc /usr/local/bin/
COPY --from=binaries /artifacts/MINIO-LICENSE /artifacts/MC-LICENSE /usr/share/doc/mathvision-storage/
COPY SOURCES.md /usr/share/doc/mathvision-storage/SOURCES.md
ENV HOME=/home/mathvision
USER 10001:10001
EXPOSE 9000
HEALTHCHECK --interval=10s --timeout=5s --retries=10 CMD curl --fail --silent http://127.0.0.1:9000/minio/health/ready || exit 1
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--console-address", ":9001"]
