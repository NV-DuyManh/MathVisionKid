"""Keep the official Colab proxy alive across local MCP client sessions."""
import asyncio
import json
import logging
import os
from pathlib import Path
import secrets
import websockets
import webbrowser
import contextlib
from urllib.parse import urlsplit,parse_qs

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from colab_mcp.session import ColabSessionProxy
import colab_mcp.session as colab_session
from colab_mcp.websocket_server import ColabWebSocketServer

class LocalIPv4WebSocketServer(ColabWebSocketServer):
    def __init__(self):
        # Windows may allocate different ephemeral ports for IPv4 and IPv6
        # when binding localhost:0. Use one loopback socket for the browser.
        super().__init__(host="127.0.0.1")
        self.reconnect_port=0
        # One supervised restart can retain the exact already-authorized local
        # connection endpoint. Origin/token checks below remain unchanged.
        seed=Path(__file__).resolve().parent/'data_only_reconnect_seed.json'
        if seed.exists():
            previous=json.loads(seed.read_text(encoding='utf-8'))
            url=urlsplit(previous['browser_connection_url'])
            if url.scheme!='https' or url.netloc!='colab.research.google.com' or url.path!='/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l':
                raise ValueError('Reconnect seed does not match intended notebook')
            fragment=parse_qs(url.fragment)
            port=int(fragment['mcpProxyPort'][0]); token=fragment['mcpProxyToken'][0]
            if not 1024<=port<=65535 or not token:raise ValueError('Invalid reconnect endpoint')
            self.reconnect_port=port;self.token=token

    async def __aenter__(self):
        # A notebook response can exceed websockets' default 1 MiB, especially
        # with code snapshots and outputs. Keep a bounded 16 MiB limit; preserve
        # loopback binding, origin checks, subprotocol and token validation.
        self._server = await websockets.serve(
            self._connection_handler, host=self.host, port=self.reconnect_port,
            subprotocols=["mcp"], origins=self.allowed_origins,
            process_request=self._validate_authorization, max_size=16 * 1024 * 1024)
        self.port = self._server.sockets[0].getsockname()[1]
        self.ipv6_server = await websockets.serve(
            self._connection_handler, host="::1", port=self.port,
            subprotocols=["mcp"], origins=self.allowed_origins,
            process_request=self._validate_authorization, max_size=16 * 1024 * 1024)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.ipv6_server.close()
        await self.ipv6_server.wait_closed()
        await super().__aexit__(exc_type, exc_val, exc_tb)

    def _validate_authorization(self, websocket, request):
        result = super()._validate_authorization(websocket, request)
        logging.info("Browser handshake: origin=%s token_matches=%s authorization_present=%s status=%s",
                     request.headers.get("Origin"), f"access_token={self.token}" in request.path,
                     bool(request.headers.get("Authorization")),
                     result.status_code if result is not None else 101)
        return result

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data_only_connection.json"
AUTH = ROOT / "local_auth.txt"
NOTEBOOK = "https://colab.research.google.com/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l"

async def await_local_proxy_connection(self):
    # wait_for(gather(..., self._start_task)) in the upstream implementation
    # cancels lifetime initialization after one UI timeout. Shield only that
    # task, so a later legitimate browser confirmation can still initialize it.
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(asyncio.gather(self.wss.connection_live.wait(),
            asyncio.shield(self._start_task)),timeout=colab_session.UI_CONNECTION_TIMEOUT)

async def main():
    # The owner explicitly selected Chrome after the previous Colab account
    # exhausted its GPU quota. Keep the official MCP connection flow, while
    # selecting the requested browser instead of the Windows default browser.
    chrome = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    if not chrome.is_file():
        raise FileNotFoundError('Requested Chrome executable unavailable')
    # The owner explicitly selected the Chrome profile named Hoai (Profile 3).
    # Route the existing official MCP browser connection to that profile.
    webbrowser.register('mathvision_chrome',None,webbrowser.BackgroundBrowser(
        [str(chrome), '--profile-directory=Profile 3', '%s']),preferred=True)
    token = AUTH.read_text().strip() if AUTH.exists() else secrets.token_urlsafe(32)
    if not AUTH.exists():
        AUTH.write_text(token, encoding="utf-8")
    logging.basicConfig(filename=ROOT / "data_only_host.log", level=logging.INFO)
    auth = StaticTokenVerifier(tokens={token: {"client_id": "codex-local", "scopes": ["colab"]}})
    server = FastMCP(name="ColabMCP", auth=auth)
    colab_session.ColabWebSocketServer = LocalIPv4WebSocketServer
    colab_session.ColabProxyClient.await_proxy_connection = await_local_proxy_connection
    colab_session.SCRATCH_PATH = "/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l"
    proxy = ColabSessionProxy()
    await proxy.start_proxy_server()
    server.mount(proxy.proxy_server)
    for middleware in proxy.middleware:
        server.add_middleware(middleware)
    @server.tool()
    async def local_colab_connection_status() -> dict:
        client=proxy.middleware[0].proxy_client
        task=client._start_task
        return {'browser':'chrome','notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',
            'websocket_connected':proxy.wss.connection_live.is_set(),
            'client_ready':client.is_connected(),'initialization_cancelled':task.cancelled(),
            'initialization_done':task.done(),'loopback_only':True}
    STATE.write_text(json.dumps({
        "pid": os.getpid(), "mcp_url": "http://127.0.0.1:8769/mcp",
        "notebook_url": NOTEBOOK,
        "browser_connection_url": f"{NOTEBOOK}#mcpProxyToken={proxy.wss.token}&mcpProxyPort={proxy.wss.port}",
    }), encoding="utf-8")
    seed=ROOT/'data_only_reconnect_seed.json'
    if seed.exists():seed.unlink()
    try:
        await server.run_async(transport="streamable-http", host="127.0.0.1", port=8769, show_banner=False)
    finally:
        await proxy.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
