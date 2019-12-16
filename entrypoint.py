#!/usr/bin/python3
import shutil
import xml.dom.minidom
from entrypoint_helpers import env, gen_cfg, str2bool, start_app, set_perms, set_ownership


RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
CONFLUENCE_INSTALL_DIR = env['confluence_install_dir']
CONFLUENCE_HOME = env['confluence_home']


SSL_ENABLED = env['atl_sslenabled']



gen_cfg('server.xml.j2', f'{CONFLUENCE_INSTALL_DIR}/conf/server.xml')
gen_cfg('seraph-config.xml.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/seraph-config.xml')
gen_cfg('confluence-init.properties.j2',
        f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/classes/confluence-init.properties')
gen_cfg('confluence.cfg.xml.j2', f'{CONFLUENCE_HOME}/confluence.cfg.xml',
        user=RUN_USER, group=RUN_GROUP, overwrite=False)

if SSL_ENABLED == 'True' or SSL_ENABLED == true or SSL_ENABLED == 'true' :
  dom = xml.dom.minidom.parse(f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/web.xml')
  new_security_constraint = dom.createElement('security-constraint')
  web_resource_collection = dom.createElement('web-resource-collection')
  web_resource_name = dom.createElement('web-resource-name')
  url_pattern = dom.createElement('url-pattern')
  restricted_urls = dom.createTextNode("Restricted URLs")
  path_url = dom.createTextNode("/")
  web_resource_name.appendChild(restricted_urls)
  url_pattern.appendChild(path_url)
  web_resource_collection.appendChild(web_resource_name)
  web_resource_collection.appendChild(url_pattern)
  user_data_constraint = dom.createElement('user-data-constraint')
  transport_guarantee = dom.createElement('transport-guarantee')
  confident =  dom.createTextNode("CONFIDENTIAL")
  transport_guarantee.appendChild(confident)
  user_data_constraint.appendChild(transport_guarantee)
  new_security_constraint.appendChild(web_resource_collection)
  new_security_constraint.appendChild(user_data_constraint)

  web_app = dom.getElementsByTagName('web-app')[0]
  web_app.appendChild(new_security_constraint)
  with open(f'{CONFLUENCE_INSTALL_DIR}/confluence/WEB-INF/web.xml', "wb") as f:
    dom.writexml(f)


set_ownership(f'{CONFLUENCE_INSTALL_DIR}/logs',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/temp',  user=RUN_USER, group=RUN_GROUP)
set_ownership(f'{CONFLUENCE_INSTALL_DIR}/work',  user=RUN_USER, group=RUN_GROUP)

shutil.chown(CONFLUENCE_HOME, user=RUN_USER, group=RUN_GROUP)

start_app(f'{CONFLUENCE_INSTALL_DIR}/bin/start-confluence.sh -fg', CONFLUENCE_HOME, name='Confluence')
