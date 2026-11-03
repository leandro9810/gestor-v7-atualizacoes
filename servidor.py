# -*- coding: utf-8 -*-
import json, os, sqlite3, threading, webbrowser, time, secrets
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

BASE=Path(__file__).resolve().parent
DB=BASE/'dados'/'gestor.sqlite3'
HOST='127.0.0.1'
PORT=0
MAX_SIZE=8_000_000
LOCK=threading.RLock()

# Identificação exclusiva da execução do Gestor
CONTROL_FILE = BASE / "gestor_controle.json"
SHUTDOWN_TOKEN = secrets.token_urlsafe(32)

def connect():
    c=sqlite3.connect(DB,timeout=15)
    c.execute('PRAGMA busy_timeout=15000')
    return c

def backup_now():
    target=BASE/'backups'
    target.mkdir(exist_ok=True)
    name='gestor_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.sqlite3'
    with LOCK:
        with connect() as src, sqlite3.connect(target/name) as dst:
            src.backup(dst)
    with sqlite3.connect(target/name) as c:
        result=c.execute('PRAGMA integrity_check').fetchone()[0]
    if result!='ok':
        (target/name).unlink(missing_ok=True)
        raise RuntimeError('Falha na integridade do backup')
    backups=sorted(target.glob('gestor_*.sqlite3'),reverse=True)
    for old in backups[30:]:
        old.unlink()
    return name

class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))
    def respond(self,status,body,kind='application/json; charset=utf-8'):
        if isinstance(body,str):body=body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/':
            return self.respond(200,(BASE/'interface.html').read_bytes(),'text/html; charset=utf-8')
        if path=='/api/data':
            with LOCK,connect() as c:
                row=c.execute('SELECT json_data FROM app_state WHERE id=1').fetchone()
            return self.respond(200,row[0] if row else '{"projects":[],"extras":[]}')
        if path=='/api/health':
            return self.respond(200,'{"ok":true}')
        if path=='/api/shutdown':
            from urllib.parse import parse_qs
            token = parse_qs(urlparse(self.path).query).get('token', [''])[0]
            if not secrets.compare_digest(token, SHUTDOWN_TOKEN):
                return self.respond(403, '{"error":"Não autorizado"}')
            self.respond(200, '{"ok":true}')
            threading.Thread(
                target=self.server.shutdown,
                daemon=True
            ).start()
            return
        self.respond(404,'{"error":"Não encontrado"}')
    def do_PUT(self):
        if urlparse(self.path).path!='/api/data':
            return self.respond(404,'{"error":"Não encontrado"}')
        origin=self.headers.get('Origin')
        expected='http://127.0.0.1:'+str(self.server.server_port)
        if origin and origin!=expected:
            return self.respond(403,'{"error":"Origem não autorizada"}')
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>MAX_SIZE: raise ValueError('Tamanho inválido')
            raw=self.rfile.read(n)
            obj=json.loads(raw)
            if not isinstance(obj,dict) or not isinstance(obj.get('projects'),list) or not isinstance(obj.get('extras'),list):
                raise ValueError('Estrutura inválida')
            with LOCK,connect() as c:
                c.execute("UPDATE app_state SET json_data=?, updated_at=datetime('now','localtime') WHERE id=1",(json.dumps(obj,ensure_ascii=False),))
                c.commit()
            self.respond(200,'{"ok":true}')
        except (ValueError,json.JSONDecodeError) as e:
            self.respond(400,json.dumps({'error':str(e)},ensure_ascii=False))
        except Exception as e:
            self.respond(500,json.dumps({'error':str(e)},ensure_ascii=False))


if __name__ == '__main__':
    with ThreadingHTTPServer((HOST, PORT), Handler) as http:
        url = f'http://{HOST}:{http.server_port}/'
        print('Gestor V7 em ' + url, flush=True)

        CONTROL_FILE.write_text(
            json.dumps({
                'port': http.server_port,
                'token': SHUTDOWN_TOKEN
            }),
            encoding='utf-8'
        )

        threading.Timer(
            0.8,
            lambda: webbrowser.open(url)
        ).start()

        try:
            http.serve_forever()
        except KeyboardInterrupt:
            pass