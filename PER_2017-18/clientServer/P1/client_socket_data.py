import socket

# create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(s)
# now connect to the web server on port 80 (the normal http port)
s.connect(("www.urjc.es", 80))
print(s)
# And now let's connect to our own server
try:
    s.connect(("localhost", 8091))
except OSError:
    print("Socket already used")
    # But first we need to disconnect
    s.close()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 8091))
print("Read from the server", s.recv(2048).decode("utf-8"))
