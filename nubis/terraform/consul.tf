# Discover Consul settings
module "consul" {
  source       = "github.com/nubisproject/nubis-terraform//consul?ref=v2.0.4"
  region       = "${var.region}"
  environment  = "${var.environment}"
  account      = "${var.account}"
  service_name = "${var.service_name}"
}

# Configure our Consul provider, module can't do it for us
provider "consul" {
  address    = "${module.consul.address}"
  scheme     = "${module.consul.scheme}"
  datacenter = "${module.consul.datacenter}"
}

# Publish our outputs into Consul for our application to consume
resource "consul_keys" "config" {
  key {
    name   = "environment"
    path   = "${module.consul.config_prefix}/ServerNameSuffix"
    value  = "${lookup(var.server_name_suffix, var.environment, lookup(var.server_name_suffix, "stage"))}"
    delete = true
  }

  key {
    name   = "site_url"
    path   = "${module.consul.config_prefix}/ServerName"
    value  = "https://iplimit.irc.${lookup(var.server_name_suffix, var.environment, lookup(var.server_name_suffix, "stage"))}"
    delete = true
  }
}
