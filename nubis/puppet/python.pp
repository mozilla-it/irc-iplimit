class { 'python':
  version => 'system',
  pip     => true,
  dev     => true,
}

class { 'mysql::bindings':
    python_enable => true,
    client_dev => true,
}

# pip install requirements
python::requirements { "/var/www/${project_name}/requirements.txt":
  forceupdate => true,
  require => [
    Class['python'],
    Class['mysql::bindings'],
  ]
}
