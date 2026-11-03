"""Serve only the two route-map HTML files on localhost; never proxy OSM tiles."""
import argparse,functools,http.server,threading,webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ALLOWED={'/Budapest_Road_Map.html','/Budapest_Hard_Stop_Map.html'}
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path=='/':self.send_response(302);self.send_header('Location','/Budapest_Road_Map.html');self.end_headers();return
        if path not in ALLOWED:self.send_error(404);return
        super().do_GET()
    def end_headers(self):
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin');super().end_headers()
def make_server(directory=ROOT):
    return http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(directory)))
def main():
    p=argparse.ArgumentParser();p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    server=make_server();url=f'http://127.0.0.1:{server.server_port}/Budapest_Road_Map.html';print(url,flush=True);print('Press Ctrl+C to stop. Online tiles are optional; click the page button to request them.',flush=True)
    if not a.no_browser:threading.Timer(.3,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
