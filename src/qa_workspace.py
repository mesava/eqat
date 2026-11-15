"""Local browser workspace for the EQAT program builder."""

import argparse
import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from qa_program_builder import FEATURE_LABELS, ROOT, generate, load, markdown, validate_catalog

ASSETS = {
    '/': ('index.html', 'text/html'),
    '/app.js': ('app.js', 'text/javascript'),
    '/style.css': ('style.css', 'text/css'),
}


class WorkspaceHandler(BaseHTTPRequestHandler):
    def reply(self, status, content, content_type):
        self.send_response(status)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(content)

    def reply_json(self, status, result):
        self.reply(status, json.dumps(result, ensure_ascii=False).encode('utf-8'), 'application/json')

    def is_local_request(self):
        local_host = f'127.0.0.1:{self.server.server_port}'
        return (self.headers.get('Host') == local_host and
                self.headers.get('Origin') in (None, f'http://{local_host}'))

    def do_GET(self):
        if not self.is_local_request():
            self.reply_json(HTTPStatus.FORBIDDEN, {'error': 'Откройте рабочее место по локальному адресу.'})
            return
        if self.path == '/api/setup':
            self.reply_json(HTTPStatus.OK, {'profiles': load('equipment_profiles.json'), 'labels': FEATURE_LABELS})
        elif self.path in ASSETS:
            filename, content_type = ASSETS[self.path]
            self.reply(HTTPStatus.OK, (ROOT / 'ui' / filename).read_bytes(), content_type)
        else:
            self.reply_json(HTTPStatus.NOT_FOUND, {'error': 'Страница не найдена.'})

    def do_POST(self):
        if not self.is_local_request():
            self.reply_json(HTTPStatus.FORBIDDEN, {'error': 'Запрос пришёл с другого адреса.'})
            return
        if self.path != '/api/program':
            self.reply_json(HTTPStatus.NOT_FOUND, {'error': 'Страница не найдена.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.headers.get_content_type() != 'application/json' or not 0 < length <= 32768:
                raise ValueError('Передайте один профиль в формате JSON.')
            profile = json.loads(self.rfile.read(length))
            if not isinstance(profile, dict) or not isinstance(profile.get('id'), str) or not profile['id'].strip():
                raise ValueError('Укажите идентификатор профиля.')
            program = generate(machines=[profile])
        except (ValueError, KeyError, TypeError) as exc:
            self.reply_json(HTTPStatus.BAD_REQUEST, {'error': f'Проверьте профиль. {exc}'})
            return
        self.reply_json(HTTPStatus.OK, {'program': program, 'markdown': markdown(program)})


def main():
    parser = argparse.ArgumentParser(description='Открыть локальное рабочее место EQAT')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true', help='Открыть страницу в браузере')
    args = parser.parse_args()
    validate_catalog()
    with ThreadingHTTPServer(('127.0.0.1', args.port), WorkspaceHandler) as server:
        url = f'http://127.0.0.1:{server.server_port}'
        print(url, flush=True)
        if args.open:
            threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
