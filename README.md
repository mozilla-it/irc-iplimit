irc-iplimit
===========

A web app to enable self-service IRC IP connection limit exception creation. Wow, what a mouthful.

Mozilla's IRC network (and many others) have a common problem where, due to spam, we have to limit the number of IRC connections allowed from a single IP address. However, we often have people getting together in groups and working from conferences, hotels, etc, and these people are often blocked from IRC until
an admin can manually add an exception. With this self-service site, they're able to add an exception on their own.

When completed and deployed, it will be protected behind an LDAP login screen.

Still pretty bare bones at the moment.

![Screenshot of iplimit in action](/screenshot.png?raw=true "iplimit in action")
