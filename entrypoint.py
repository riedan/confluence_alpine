#!/usr/bin/python3
import shutil

from entrypoint_helpers import env, gen_cfg, str2bool, start_app, set_perms, set_ownership, activate_ssl, sed


RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
CONFLUENCE_INSTALL_DIR = env['confluence_install_dir']
CONFLUENCE_HOME = env['confluence_home']
CONFLUENCE_CFG_OVERWRITE =  env.get('atl_confluence_cfg_overwrite', False)
CONFLUENCE_TLS_PROTOCOLS = env.get('atl_confluence_tls_protocols', 'TLSv1.1,TLSv1.2')

SSL_ENABLED = env['atl_sslenabled']

sed('TLSv1.1,TLSv1.2', CONFLUENCE_TLS_PROTOCOLS, f'{CONFLUENCE_INSTALL_DIR}/bin/setenv.sh')

if SSL_ENABLED == 'True' or SSL_ENABLED == True or SSL_ENABLED == 'true' :
    PATH_KEYSTORE = env.get('atl_certificate_location', '/opt/atlassian/confluence/keystore')
    PASSWORD_KEYSTORE = env.get('atl_certificate_password', "changeit")

    PATH_CERTIFICATE_KEY = env.get('atl_certificate_key_location', '/opt/atlassian/etc/certificate.key')
    PATH_CERTIFICATE = env.get('atl_certificate_location', '/opt/atlassian/etc/certificate.crt')
    PATH_CA = env.get('atl_ca_location','/opt/atlassian/etc/ca.cert')

    PATH_P12= env.get('atl_p12_location', '/opt/atlassian/etc/certificate.p12')
    PASSWORD_P12 = env.get('atl_p12_password', 'confluence')

    activate_ssl( f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/web.xml', PATH_KEYSTORE, PASSWORD_KEYSTORE, PATH_CERTIFICATE_KEY, PATH_CERTIFICATE, PATH_CA, PASSWORD_P12, PATH_P12)

gen_cfg('server.xml.j2', f'{CONFLUENCE_INSTALL_DIR}/conf/server.xml')
gen_cfg('seraph-config.xml.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/seraph-config.xml')
gen_cfg('confluence-init.properties.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/confluence-init.properties')
gen_cfg('confluence.cfg.xml.j2', f'{CONFLUENCE_HOME}/confluence.cfg.xml',
        user=RUN_USER, group=RUN_GROUP, overwrite=CONFLUENCE_CFG_OVERWRITE)




set_ownership(f'{CONFLUENCE_INSTALL_DIR}/logs',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/temp',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/work',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/conf',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/bin',  user=RUN_USER, group=RUN_GROUP)

shutil.chown(CONFLUENCE_HOME, user=RUN_USER, group=RUN_GROUP)


start_app(f'{CONFLUENCE_INSTALL_DIR}/bin/start-confluence.sh -fg', CONFLUENCE_HOME, name='Confluence')
