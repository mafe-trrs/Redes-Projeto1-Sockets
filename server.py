import http.server
import socketserver

PORT = 8000 

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Servidor rodando na porta", PORT)
    print("Acesse http://localhost:8000 no seu navegador")
    httpd.serve_forever()
