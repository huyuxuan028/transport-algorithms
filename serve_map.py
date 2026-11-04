"""Serve the generated shared route map on localhost, with a normal browser referrer."""
import argparse
import functools
import http.server
import threading
import webbrowser
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?', 1)[0] not in ['/', '/Shared_Road_Map.html']:
            self.send_error(404)
            return
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/Shared_Road_Map.html')
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        super().end_headers()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, default=Path('generated'))
    p.add_argument('--no-browser', action='store_true')
    a = p.parse_args()
    if not (a.directory/'Shared_Road_Map.html').is_file():
        p.error('Generate Shared_Road_Map.html with map_shared_routes.py first')
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0),
        functools.partial(Handler, directory=str(a.directory.resolve())))
    url = f'http://127.0.0.1:{server.server_port}/Shared_Road_Map.html'
    print(url, flush=True)
    if not a.no_browser:
        threading.Timer(.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
