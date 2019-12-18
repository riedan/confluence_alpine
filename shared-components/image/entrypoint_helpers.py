import sys
import os
import shutil
import logging
import jinja2 as j2
import uuid
import base64
import xml.dom.minidom
import subprocess
from subprocess import call

logging.basicConfig(level=logging.DEBUG)


######################################################################
# Setup inputs and outputs

# Import all ATL_* and Dockerfile environment variables. We lower-case
# these for compatability with Ansible template convention. We also
# support CATALINA variables from older versions of the Docker images
# for backwards compatability, if the new version is not set.
env = {k.lower(): v
       for k, v in os.environ.items()}


# Setup Jinja2 for templating
jenv = j2.Environment(
    loader=j2.FileSystemLoader('/opt/atlassian/etc/'),
    autoescape=j2.select_autoescape(['xml']))


######################################################################
# Utils

def set_perms(path, user, group, mode):
    shutil.chown(path, user=user, group=group)
    os.chmod(path, mode)
    for dirpath, dirnames, filenames in os.walk(path):
        shutil.chown(dirpath, user=user, group=group)
        os.chmod(dirpath, mode)
        for filename in filenames:
            shutil.chown(os.path.join(dirpath, filename), user=user, group=group)
            os.chmod(os.path.join(dirpath, filename), mode)


def set_ownership(path, user, group):
    shutil.chown(path, user=user, group=group)
    for dirpath, dirnames, filenames in os.walk(path):
        shutil.chown(dirpath, user=user, group=group)
        for filename in filenames:
            shutil.chown(os.path.join(dirpath, filename), user=user, group=group)

def check_perms(path, uid, gid, mode):
    stat = os.stat(path)
    return all([
        stat.st_uid == int(uid),
        stat.st_gid == int(gid),
        stat.st_mode & mode == mode
    ])

def gen_cfg(tmpl, target, user='root', group='root', mode=0o644, overwrite=True):
    if not overwrite and os.path.exists(target):
        logging.info(f"{target} exists; skipping.")
        return

    logging.info(f"Generating {target} from template {tmpl}")
    cfg = jenv.get_template(tmpl).render(env)
    try:
        with open(target, 'w') as fd:
            fd.write(cfg)
    except (OSError, PermissionError):
        logging.warning(f"Container not started as root. Bootstrapping skipped for '{target}'")
    else:
        set_perms(target, user, group, mode)

def gen_container_id():
    env['uuid'] = uuid.uuid4().hex
    with open('/etc/container_id') as fd:
        lcid = fd.read()
        if lcid != '':
            env['local_container_id'] = lcid

def str2bool(v):
    if str(v).lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    return False


def activate_ssl(web_path, path_keystore, password_keystore, path_key, path_crt, path_ca, password_p12, path_p12):
    dom = xml.dom.minidom.parse(web_path)

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

    with open(web_path, "wb") as f:
        dom.writexml(f)

    if os.path.exists(path_crt) and os.path.exists(path_key)  and os.path.exists(path_ca) and not os.path.exists(path_p12):
        myP12 = call(['openssl', 'pkcs12', '-in', path_crt, '-inkey', path_key, '-CAfile', path_ca, '-name', 'confluence','' "-out", path_p12 , '-password',  'pass:' + password_p12])

    if os.path.exists(path_p12) and not os.path.exists(password_keystore):
        myKeystore = call(['keytool', '-importkeystore', '-srckeystore' ,  path_p12,'-srcstoretype', 'pkcs12',  '-srcalias', '1', '-srcstorepass', password_p12, ' -destkeystore', 'path_keystore', '-deststoretype' , 'jks', '-deststorepass', password_keystore, '-destkeypass', password_keystore,  '-destalias', 'host_identity'])


######################################################################
# Start App as the correct user

def start_app(start_cmd, home_dir, name='app'):
    if os.getuid() == 0:
        if str2bool(env.get('set_permissions') or True) and check_perms(home_dir, env['run_uid'], env['run_gid'], 0o700) is False:
            set_perms(home_dir, env['run_user'], env['run_group'], 0o700)
            logging.info(f"User is currently root. Will change directory ownership and downgrade run user to to {env['run_user']}")
        else:
            logging.info(f"User is currently root. Will downgrade run user to to {env['run_user']}")

        cmd = '/bin/su'
        args = [cmd, env['run_user'], '-c', start_cmd]
    else:
        cmd = '/bin/sh'
        args = [cmd, '-c', start_cmd]

    logging.info(f"Running {name} with command '{cmd}', arguments {args}")
    os.execv(cmd, args)