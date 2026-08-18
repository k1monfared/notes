---
tags: linux, sftp
---

# sftp stories

When I was at WIU I had this website on their server that I had to maintain through their sftp server. It's been a while I have forgotten how to connect to do it. So, I am rediscovering it step by step, and here is a map for later!

	- Connect to their VPN:

	<li>Currently they use a cisco vpn client (Cisco AnyConnect Security Mobility Client Version 3.1.12020 Copyright (c) 2004 - 2015 Cisco Systems).
	- Connect to vpn.wiu.edu with ECom username and password

</li>
	- Connect to sftp server:

	<li>In a file browser type: sftp://sftp.wiu.edu
Here I get the following error:
Oops! Something went wrong.
Unhandled error message: SSH program unexpectedly exited
	- A google search tells me that it might be due my IP not being in a whitelist that the server uses. It is a little weird if that is the case, sice I'm connected to their vpn and I should be assigned a local IP address. I've contacted them to see what the case is.
	- It turns out that they had restricted my user since I'm not a faculty member any more. But I got access for a week to update my page to link to my current page. The above command worked.

</li>
