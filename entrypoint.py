#!/usr/bin/python3
import shutil
from entrypoint_helpers import env, gen_cfg, str2bool, start_app, set_perms, set_ownership


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
        user=RUN_USER, group=RUN_GROUP, overwrite=True)

gen_cfg('web.xml.j2', f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/web.xml')


set_ownership(f'{CONFLUENCE_INSTALL_DIR}/logs',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/temp',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/work',  user=RUN_USER, group=RUN_GROUP)

shutil.chown(CONFLUENCE_HOME, user=RUN_USER, group=RUN_GROUP)

start_app(f'{CONFLUENCE_INSTALL_DIR}/bin/start-confluence.sh -fg', CONFLUENCE_HOME, name='Confluence')
