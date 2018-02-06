module "worker" {
  source            = "github.com/nubisproject/nubis-terraform//worker?ref=v2.0.4"
  region            = "${var.region}"
  environment       = "${var.environment}"
  account           = "${var.account}"
  service_name      = "${var.service_name}"
  purpose           = "webserver"
  ami               = "${var.ami}"
  elb               = "${module.load_balancer.name}"
  ssh_key_file      = "${var.ssh_key_file}"
  ssh_key_name      = "${var.ssh_key_name}"
  nubis_sudo_groups = "${var.nubis_sudo_groups}"
  nubis_user_groups = "${var.nubis_user_groups}"
  wait_for_capacity_timeout = "20m"
  health_check_grace_period = "600"
}

module "database" {
  source                 = "github.com/nubisproject/nubis-terraform//database?ref=v2.0.4"
  region                 = "${var.region}"
  environment            = "${var.environment}"
  account                = "${var.account}"
  monitoring             = true
  service_name           = "${var.service_name}"
  client_security_groups = "${module.worker.security_group}"
}

module "load_balancer" {
  source               = "github.com/nubisproject/nubis-terraform//load_balancer?ref=v2.0.4"
  region               = "${var.region}"
  environment          = "${var.environment}"
  account              = "${var.account}"
  service_name         = "${var.service_name}"
  health_check_target  = "HTTP:80/health"
  ssl_cert_name_prefix = "${var.service_name}"
}

module "dns" {
  source       = "github.com/nubisproject/nubis-terraform//dns?ref=v2.0.4"
  region       = "${var.region}"
  environment  = "${var.environment}"
  account      = "${var.account}"
  service_name = "${var.service_name}"
  target       = "${module.load_balancer.address}"
}
