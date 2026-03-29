from urllib.parse import urlunparse

def nls_meta_endpoint_from_region(region: str) -> str:
    return f"http://nls-meta.{region}.aliyuncs.com"

def nls_websocket_endpoint_from_region(region: str = 'cn-shanghai') -> str:
    protocol = 'wss'
    hostname = f"nls-gateway.{region}.aliyuncs.com"
    port = None

    if region in ['cn-shanghai-internal', 'cn-beijing-internal', 'cn-shenzhen-internal']:
        # For internal regions, the hostname is like nls-gateway-cn-shanghai-internal.aliyuncs.com
        hostname = f"nls-gateway-{region}.aliyuncs.com"
        port = 80

    netloc = hostname
    if port:
        netloc = f"{hostname}:{port}"

    return urlunparse((protocol, netloc, '/ws/v1', '', '', ''))
