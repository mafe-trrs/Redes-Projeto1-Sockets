import http.client

HOST = 'localhost'
PORT = 8000 

conn = http.client.HTTPConnection(HOST, PORT)
conn.request('GET', '/index.html')

r1 = conn.getresponse()
print(f"Status: {r1.status} {r1.reason}") 

headers = r1.getheaders()
print("\n--- Headers ---")
for name, value in headers:
    print(f"{name}: {value}")

data = r1.read().decode('utf-8')
print("\n--- Conteúdo ---")
print(data)
    
conn.close()
