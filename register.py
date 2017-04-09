#!/usr/bin/env python
import sys, os
from mastodon import Mastodon

if(len(sys.argv)<=4):
	print("Usage: register clientName instanceUrl email password")
	sys.exit(1)

(clientName, instanceUrl, email, password) = sys.argv[1:]

clientCredFname="_".join([clientName, instanceUrl.replace("https://", "").replace("/", ""), "clientcred.txt"])
userCredFname="_".join([clientName, instanceUrl.replace("https://", "").replace("/", ""), email, "clientcred.txt"])

if not (os.path.exists(clientCredFname)):
	Mastodon.create_app(clientName, to_file=clientCredFname, api_base_url=instanceUrl)

mastodon = Mastodon(client_id=clientCredFname, api_base_url=instanceUrl)
mastodon.log_in(email, password, to_file=userCredFname)

