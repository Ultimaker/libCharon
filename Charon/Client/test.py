import sys

import Charon.Client

if len(sys.argv) != 2:
    print("Usage: test.py [file]")
    exit(1)

request = Charon.Client.Request(sys.argv[1], "/Metadata/thumbnail.png")
request.waitForFinished()

if request.state == Charon.Client.Request.State.Completed:
    print("Completed successfully")
    print(request.data)
else:
    print("Error")
    print(request.errorString)
