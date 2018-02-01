import sys

from PyQt5.QtCore import QCoreApplication, QTimer

import Charon.Client

if len(sys.argv) != 2:
    print("Usage: test.py [file]")
    exit(1)

app = QCoreApplication(sys.argv)

request = Charon.Client.Request(sys.argv[1], ["/Metadata/thumbnail.png"])
request.start()

while(request.state == Charon.Client.Request.State.Running):
    app.processEvents()

if request.state == Charon.Client.Request.State.Completed:
    print("Request Complete")
    print(request.data)
elif request.state == Charon.Client.Request.State.Error:
    print("Request Error")
    print(request.errorString)
else:
    print("Request did not finish properly")
    print(request.state)
