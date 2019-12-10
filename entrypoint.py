#!/usr/bin/python3

from entrypoint_helpers import env, gen_cfg, str2bool, start_app, set_perms


RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
CONFLUENCE_INSTALL_DIR = env['confluence_install_dir']
CONFLUENCE_HOME = env['confluence_home']

gen_cfg('server.xml.j2', f'{CONFLUENCE_INSTALL_DIR}/conf/server.xml')
gen_cfg('seraph-config.xml.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/seraph-config.xml')
gen_cfg('confluence-init.properties.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/confluence-init.properties')
gen_cfg('confluence.cfg.xml.j2', f'{CONFLUENCE_HOME}/confluence.cfg.xml',
        user=RUN_USER, group=RUN_GROUP, overwrite=False)

gen_cfg('web.xml.j2', f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/web.xml',
        user=RUN_USER, group=RUN_GROUP, overwrite=False)


set_perms('{CONFLUENCE_INSTALL_DIR}/conf', RUN_USER, RUN_GROUP, 700)
set_perms('{CONFLUENCE_INSTALL_DIR}/logs', RUN_USER, RUN_GROUP, 700)
set_perms('{CONFLUENCE_INSTALL_DIR}/temp', RUN_USER, RUN_GROUP, 700)
set_perms('{CONFLUENCE_INSTALL_DIR}/work', RUN_USER, RUN_GROUP, 700)
set_perms('{CONFLUENCE_HOME}', RUN_USER, RUN_GROUP, 700)

start_app(f'{CONFLUENCE_INSTALL_DIR}/bin/start-confluence.sh -fg', CONFLUENCE_HOME, name='Confluence')
