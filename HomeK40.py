
from k40nano import NanoConnection

with NanoConnection() as stream:
    stream.write("IPP")
