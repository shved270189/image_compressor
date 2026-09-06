"""Serve synthetic download probes only; never receive or serve user images."""

import argparse
import hashlib
import struct
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


def fixture():
    rows = b''.join(b'\0' + hashlib.shake_256(str(y).encode()).digest(3072) for y in range(1024))
    header = struct.pack('!2I5B', 1024, 1024, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


PNG = fixture()
HTML = Path(__file__).with_suffix('.html').read_bytes()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, content, media):
        self.send_response(status)
        self.send_header('Content-Type', media)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == '/':
            self.reply(200, HTML, 'text/html; charset=utf-8')
        elif self.path == '/fixture.png':
            self.reply(200, PNG, 'image/png')
        else:
            self.reply(404, b'Not found', 'text/plain')

    def do_POST(self):
        parts = urlsplit(self.path)
        if parts.path != '/result' or self.headers.get('Content-Length', '0') != '0':
            self.close_connection = True
            self.reply(400, b'Only empty synthetic requests are accepted', 'text/plain')
            return
        scenario = parse_qs(parts.query).get('scenario', ['success'])[0]
        if scenario == 'failure':
            self.reply(500, b'Synthetic failure', 'text/plain')
            return
        if scenario == 'slow':
            time.sleep(8)
        try:
            if scenario == 'truncated':
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(PNG)))
                self.end_headers()
                self.wfile.write(PNG[:100])
                self.close_connection = True
            else:
                self.reply(200, PNG, 'image/png')
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    print(f'PNG: {len(PNG)} bytes; SHA-256 {hashlib.sha256(PNG).hexdigest()}', flush=True)
    print(f'Probe: http://{args.bind}:{args.port}', flush=True)
    ThreadingHTTPServer((args.bind, args.port), Handler).serve_forever()
