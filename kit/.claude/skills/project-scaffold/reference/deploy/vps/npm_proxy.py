#!/usr/bin/env python3
"""Cấu hình Nginx Proxy Manager qua API (chạy TRÊN server, chỉ thư viện chuẩn).

    ssh deploy@HOST "python3 - --domain app.example.com --forward-host my-app-gateway \
        --email admin@example.com --password '...' --ssl" < deploy/vps/npm_proxy.py

Lần đầu: tự tạo tài khoản admin NPM. Sau đó: tạo/cập nhật proxy host và (tuỳ chọn) xin SSL Let's Encrypt.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

API = "http://127.0.0.1:81/api"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict | list:
    request = urllib.request.Request(f"{API}{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"NPM API {method} {path} lỗi {error.code}: {error.read().decode(errors='replace')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True)
    parser.add_argument("--forward-host", required=True)
    parser.add_argument("--forward-port", type=int, default=80)
    parser.add_argument("--email", required=True, help="Email admin NPM, cũng dùng cho Let's Encrypt")
    parser.add_argument("--password", required=True)
    parser.add_argument("--ssl", action="store_true", help="Xin chứng chỉ Let's Encrypt và bật HTTPS")
    args = parser.parse_args()

    if not call("GET", "/").get("setup"):
        call("POST", "/users", {"name": "Admin", "nickname": "Admin", "email": args.email, "roles": ["admin"],
                                "is_disabled": False, "auth": {"type": "password", "secret": args.password}})
        print("Đã tạo tài khoản admin Nginx Proxy Manager")
    token = call("POST", "/tokens", {"identity": args.email, "secret": args.password})["token"]

    host_body = {"domain_names": [args.domain], "forward_scheme": "http", "forward_host": args.forward_host,
                 "forward_port": args.forward_port, "block_exploits": True, "allow_websocket_upgrade": True,
                 "access_list_id": 0, "caching_enabled": False, "advanced_config": "", "locations": [],
                 "meta": {}}
    hosts = call("GET", "/nginx/proxy-hosts", token=token)
    existing = next((h for h in hosts if args.domain in h["domain_names"]), None)
    if existing:
        host = call("PUT", f"/nginx/proxy-hosts/{existing['id']}", host_body, token)
        print(f"Đã cập nhật proxy host {args.domain} -> {args.forward_host}:{args.forward_port}")
    else:
        host = call("POST", "/nginx/proxy-hosts", {**host_body, "certificate_id": 0, "ssl_forced": False}, token)
        print(f"Đã tạo proxy host {args.domain} -> {args.forward_host}:{args.forward_port}")

    if args.ssl:
        certificates = call("GET", "/nginx/certificates", token=token)
        certificate = next((c for c in certificates if args.domain in c["domain_names"]), None)
        if certificate is None:
            print("Đang xin chứng chỉ Let's Encrypt (domain phải trỏ đúng IP server)...")
            certificate = call("POST", "/nginx/certificates", {
                "provider": "letsencrypt", "nice_name": args.domain, "domain_names": [args.domain],
                "meta": {"letsencrypt_email": args.email, "letsencrypt_agree": True, "dns_challenge": False}},
                token)
        call("PUT", f"/nginx/proxy-hosts/{host['id']}", {
            "certificate_id": certificate["id"], "ssl_forced": True, "http2_support": True,
            "hsts_enabled": True, "hsts_subdomains": False}, token)
        print(f"✅ HTTPS đã bật cho https://{args.domain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
