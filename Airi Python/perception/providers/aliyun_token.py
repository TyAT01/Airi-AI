import hmac
import hashlib
import base64
import time
import uuid
import httpx
from datetime import datetime, timezone
from urllib.parse import quote, urlencode
from typing import Dict, Any, Optional
from perception.providers.aliyun_utils import nls_meta_endpoint_from_region

SIGNING_METHOD = 'HMAC-SHA1'
SIGNATURE_VERSION = '1.0'
API_VERSION = '2019-02-28'

def canonicalize_query(params: Dict[str, str]) -> str:
    sorted_keys = sorted(params.keys())
    return '&'.join(f"{quote(key)}={quote(params[key])}" for key in sorted_keys)

def create_string_to_sign(method: str, path: str, canonical_query: str) -> str:
    encoded_path = quote(path, safe='')
    encoded_query = quote(canonical_query, safe='')
    return f"{method}&{encoded_path}&{encoded_query}"

def sign_string_to_base64(string_to_sign: str, access_key_secret: str) -> str:
    key = (access_key_secret + '&').encode('utf-8')
    data = string_to_sign.encode('utf-8')
    signature = hmac.new(key, data, hashlib.sha1).digest()
    return base64.b64encode(signature).decode('utf-8')

async def build_create_token_request(access_key_id: str, access_key_secret: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    now = options.get('timestamp') or datetime.now(timezone.utc)

    # ISO 8601 format: YYYY-MM-DDThh:mm:ssZ
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    signature_nonce = options.get('signature_nonce') or str(uuid.uuid4())
    region_id = options.get('region_id') or 'cn-shanghai'

    params = {
        'AccessKeyId': access_key_id,
        'Action': 'CreateToken',
        'Format': 'JSON',
        'RegionId': region_id,
        'SignatureMethod': SIGNING_METHOD,
        'SignatureNonce': signature_nonce,
        'SignatureVersion': SIGNATURE_VERSION,
        'Timestamp': timestamp,
        'Version': API_VERSION,
    }
    if 'extra_query' in options:
        params.update(options['extra_query'])

    canonical_query = canonicalize_query(params)
    string_to_sign = create_string_to_sign('POST', '/', canonical_query)
    signature_base64 = sign_string_to_base64(string_to_sign, access_key_secret)
    encoded_signature = quote(signature_base64, safe='')
    signed_query = f"Signature={encoded_signature}&{canonical_query}"

    endpoint = options.get('endpoint') or nls_meta_endpoint_from_region(region_id)
    endpoint = endpoint.rstrip('/')
    url = f"{endpoint}/?{signed_query}"

    return {
        'endpoint': endpoint,
        'canonical_query': canonical_query,
        'string_to_sign': string_to_sign,
        'signature': signature_base64,
        'encoded_signature': encoded_signature,
        'signed_query': signed_query,
        'params': {**params, 'Signature': signature_base64},
        'url': url,
    }

async def create_token(access_key_id: str, access_key_secret: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    request_info = await build_create_token_request(access_key_id, access_key_secret, options)

    async with httpx.AsyncClient() as client:
        response = await client.post(request_info['url'])
        data = response.json()

    if 'Token' in data and isinstance(data['Token'], dict) and 'Id' in data['Token']:
        return {
            'token': data['Token']['Id'],
            'expires_at': data['Token']['ExpireTime'] * 1000
        }

    raise RuntimeError(f"Failed to create token: {json.dumps(data) if 'data' in locals() else 'Unknown error'}")
