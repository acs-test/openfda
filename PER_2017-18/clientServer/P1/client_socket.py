import socket

# create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(s)
# now connect to the web server on port 80 (the normal http port)
s.connect(("www.urjc.es", 80))
print(s)
