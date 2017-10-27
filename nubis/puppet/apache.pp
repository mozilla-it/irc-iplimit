class { 'nubis_apache':
}

# Add modules
class { 'apache::mod::rewrite': }
class { 'apache::mod::wsgi': }

class { 'apache::mod::auth_mellon':
  require => [
    Package['liblasso3'],
  ],
}

class { 'apt': }

# Include Houzafa Abbasbhay's PPA repo
apt::ppa { 'ppa:houzefa-abba/lasso': }

# Install newer liblasso than 2.4.0 to work around a known issue
package { 'liblasso3':
  ensure => '2.5.1-1~eob80+1+~ubuntu14.04~xcg.ppa1',
  require => [
    Apt::Ppa['ppa:houzefa-abba/lasso'],
  ],
}

file { '/etc/apache2/mellon':
  ensure => directory,
  owner  => root,
  group  => root,
  mode   => '0755',
}

apache::vhost { $project_name:
    servername                  => false,
    port                        => 80,
    default_vhost               => true,
    docroot                     => "/var/www/${project_name}",
    docroot_owner               => 'root',
    docroot_group               => 'root',
    block                       => ['scm'],

    additional_includes         => [
      '/etc/apache2/conf.d/servername.conf',
    ],

    setenvif                    => [
      'X-Forwarded-Proto https HTTPS=on',
      'Remote_Addr 127\.0\.0\.1 internal',
      'Remote_Addr ^10\. internal',
    ],

    wsgi_process_group          => $project_name,
    wsgi_script_aliases         => { '/' => "/var/www/${project_name}/iplimit.wsgi" },
    wsgi_daemon_process         => $project_name,
    wsgi_daemon_process_options => {
      processes        => 1,
      threads          => 1,
      maximum-requests => 200,
      display-name     => $project_name,
      python-path      => "/var/www/${project_name}",
      home             => "/var/www/${project_name}",
    },

    aliases                     => [
      {
        alias => '/health',
        path  => '/var/run/motd.dynamic',
      }
    ],

    directories                 => [
      {
        path                       => '/',
        provider                   => 'location',

        mellon_enable              => 'auth',
        mellon_endpoint_path       => '/mellon',

        auth_type                  => 'Mellon',
        auth_require               => 'valid-user',

        mellon_sp_private_key_file => '/etc/apache2/mellon/auth0.key',
        mellon_sp_cert_file        => '/etc/apache2/mellon/auth0.cert',
        mellon_sp_metadata_file    => '/etc/apache2/mellon/auth0.xml',
        mellon_idp_metadata_file   => '/etc/apache2/mellon/auth0.idp-metadata.xml',

        #XXX: Module doesn't support these yet
        custom_fragment            => "
    MellonSecureCookie On
    MellonSubjectConfirmationDataAddressCheck Off
        ",
      },
      {
        path          => '/health',
        provider      => 'location',
        auth_type     => 'None',
        mellon_enable => 'off',
      },
      {
        path          => '/server-status',
        provider      => 'location',
        auth_type     => 'None',
        mellon_enable => 'off',
        order         => 'allow,deny',
        allow         => 'from 127.0.0.1',
      },
      {
        path     => '/mellon',
        provider => 'location',
  auth_type      => 'None',
      },
      {
        path           => '/json',
        provider       => 'location',
        mellon_enable  => 'off',
        auth_name      => 'Secret',
        auth_type      => 'Basic',
        auth_require   => 'user json',
        auth_user_file => "/etc/${project_name}.htpasswd",
      },
    ],

    access_log_env_var => '!internal',
    access_log_format  => '%a %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"',
    custom_fragment    => "
    # Don't set default expiry on anything
    ExpiresActive Off
",
    headers                     => [
      # Nubis headers
      "set X-Nubis-Version ${project_version}",
      "set X-Nubis-Project ${project_name}",
      "set X-Nubis-Build   ${packer_build_name}",

      # Security Headers
      'set X-Content-Type-Options "nosniff"',
      'set X-XSS-Protection "1; mode=block"',
      'set X-Frame-Options "DENY"',
      'set Strict-Transport-Security "max-age=31536000"',
    ],
    rewrites                    => [
      {
        comment      => 'HTTPS redirect',
        rewrite_cond => ['%{HTTP:X-Forwarded-Proto} =http'],
        rewrite_rule => ['. https://%{HTTP:Host}%{REQUEST_URI} [L,R=permanent]'],
      }
    ]
}
