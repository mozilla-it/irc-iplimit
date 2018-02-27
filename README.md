# IRC iplimit Nubis deployment repository

This is the deployment repository for
[iplimit.irc.mozilla.org](https://iplimit.irc.mozilla.org)

A web app to enable self-service IRC IP connection limit exception creation. Wow, what a mouthful.

Mozilla's IRC network (and many others) have a common problem where, due to spam, we have to limit
the number of IRC connections allowed from a single IP address. However, we often have people getting
together in groups and working from conferences, hotels, etc, and these people are often blocked from
IRC until an admin can manually add an exception. With this self-service site, they're able to add an
exception on their own.

![Screenshot of iplimit in action](/screenshot.png?raw=true "iplimit in action")

## Components

Defined in [nubis/terraform/main.tf](nubis/terraform)

### Webservers

Defined in [nubis/puppet/apache.pp](nubis/puppet)

The produced image is that of a simple Ubuntu Apache webserver running Python/mod_wsgi

### Load Balancer

Simple ELB

### SSO

This entire application is protected behind [mod_auth_openidc](https://github.com/zmartzone/mod_auth_openidc)
except for a small JSON API dump endpoint under /json, protected by basic authentication

### Database

Main application state is persisted in an RDS/MySQL database

Administrative access to it can be gained thru the db-admin service.

### Cache

Elasticache/Memcache is used to provide persistency for mod_auth_openidc's session cache

## Configuration

The application's configuration file is
[/var/www/${project_name}/${project_name}.conf](nubis/puppet/files/confd/templates)
and is confd managed.

### Consul Keys

This application's Consul keys, living under
*${project_name}-${environment}/${environment}/config/*
and defined in Defined in [nubis/terraform/consul.tf](nubis/terraform)

#### Password

*Operator Supplied* Apache htaccess content used to control access to the JSON
endpoint

#### Cache/Endpoint

DNS endpoint of Elasticache/memcache

#### Cache/Port

TCP port of Elasticache/memcache

#### Database/Name

The name of the RDS/MySQL Database

#### Database/Password

The password to the RDS/MySQL Database

#### Database/User

The username to the RDS/MySQL Database

#### Database/Server

The hostname of the RDS/MySQL Database

#### OpenID/Server/Memcached

Hostname:Port of Elasticache/memcache

#### OpenID/Server/Passphrase

*Generated* OpenID passphrase for session encryption

#### OpenID/Client/Domain

*Operator Supplied* Auth0 Domain for this application, typically 'mozilla'

#### OpenID/Client/ID

*Operator Supplied* Auth0 Client ID for this application

#### OpenID/Client/Secret

*Operator Supplied* Auth0 Client Secret for this application 'mozilla'

#### OpenID/Client/Site

*Operator Supplied* Auth0 Site URL for this application

## Cron Jobs

None

## Logs

No application specific logs
