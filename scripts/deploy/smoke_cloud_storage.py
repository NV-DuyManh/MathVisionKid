"""Check the cloud storage image in isolated, disposable Docker resources."""
from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import time
import uuid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="mathvision-storage:cloud")
    parser.add_argument("--platform", choices=("linux/amd64", "linux/arm64"), required=True)
    args = parser.parse_args()
    prefix = "mathvision-storage-smoke-" + uuid.uuid4().hex
    environment = dict(os.environ, MINIO_ROOT_USER="storage-smoke", MINIO_ROOT_PASSWORD=secrets.token_hex(32))

    def docker(*arguments: str) -> str:
        result = subprocess.run(["docker", *arguments], env=environment, text=True,
                                capture_output=True, check=True)
        return result.stdout.strip()

    network_id = volume_name = container_id = None
    try:
        network_id = docker("network", "create", prefix)
        volume_name = docker("volume", "create", prefix)
        container_id = docker("run", "-d", "--platform", args.platform, "--name", prefix,
                              "--network", network_id, "--network-alias", "storage",
                              "--env", "MINIO_ROOT_USER", "--env", "MINIO_ROOT_PASSWORD",
                              "--mount", f"type=volume,source={volume_name},target=/data", args.image)

        def wait_ready() -> None:
            for _ in range(90):
                state = docker("inspect", "--format", "{{.State.Health.Status}}", container_id)
                if state == "healthy":
                    return
                if docker("inspect", "--format", "{{.State.Running}}", container_id) != "true":
                    raise RuntimeError("The isolated storage server stopped before becoming healthy.")
                time.sleep(1)
            raise RuntimeError("The isolated storage server did not become healthy within 90 seconds.")

        def client(command: str) -> str:
            return docker("run", "--rm", "--platform", args.platform, "--network", network_id,
                          "--env", "MINIO_ROOT_USER", "--env", "MINIO_ROOT_PASSWORD",
                          "--entrypoint", "/bin/sh", args.image, "-ec",
                          'mc alias set private http://storage:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null; ' + command)

        wait_ready()
        if docker("inspect", "--format", "{{.Config.User}}", container_id) != "10001:10001":
            raise RuntimeError("The storage server must run as the dedicated non-root user.")
        client("mc mb private/mathvision >/dev/null; mc anonymous set none private/mathvision >/dev/null; "
               "printf 'cloud-storage-roundtrip' | mc pipe private/mathvision/smoke.txt >/dev/null")
        if client("mc cat private/mathvision/smoke.txt") != "cloud-storage-roundtrip":
            raise RuntimeError("The authenticated object round trip failed.")
        if client("curl --silent --output /dev/null --write-out '%{http_code}' http://storage:9000/mathvision/smoke.txt") != "403":
            raise RuntimeError("Anonymous object access was not denied.")
        docker("restart", container_id)
        wait_ready()
        if client("mc cat private/mathvision/smoke.txt") != "cloud-storage-roundtrip":
            raise RuntimeError("The object was not retained after server restart.")
        print(f"PASS: {args.platform} storage is non-root; authenticated upload/read, anonymous denial and restart persistence verified.")
    finally:
        # Only resources returned by this invocation are removed. Production is never selected.
        if container_id:
            docker("rm", "--force", container_id)
        if volume_name:
            docker("volume", "rm", volume_name)
        if network_id:
            docker("network", "rm", network_id)


if __name__ == "__main__":
    main()
