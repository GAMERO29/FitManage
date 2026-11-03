# Colector OTLP falso: acepta las trazas y responde 200, para medir el costo de serializar y enviar.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class R(BaseHTTPRequestHandler):
    recibidos = 0
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        R.recibidos += 1
        self.send_response(200); self.send_header("Content-Type", "application/x-protobuf"); self.end_headers()
    def log_message(self, *a): pass
ThreadingHTTPServer(("127.0.0.1", 4318), R).serve_forever()
