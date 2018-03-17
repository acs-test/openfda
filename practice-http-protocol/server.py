import http.server
import socketserver

PORT = 8000

# HTTPRequestHandler class
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Send message back to client
        message = "Hello world! " + self.path
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

Handler = http.server.SimpleHTTPRequestHandler
Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()

# https://github.com/joshmaker/simple-python-webserver/blob/master/server.py
