import socketserver

import web

##
# WEB SERVER
##

PORT = 8000


# Class to handle the HTTP requests from web clients
Handler = web.OpenFDAHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()
