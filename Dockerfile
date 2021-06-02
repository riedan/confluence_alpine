FROM adoptopenjdk/openjdk8:jdk8u275-b01-alpine

ENV RUN_USER                                        confluence
ENV RUN_GROUP                                       confluence

ENV RUN_UID                                         2002
ENV RUN_GID                                         2002

# https://confluence.atlassian.com/doc/confluence-home-and-other-important-directories-590259707.html
ENV CONFLUENCE_HOME                                 /var/atlassian/application-data/confluence
ENV CONFLUENCE_INSTALL_DIR                          /opt/atlassian/confluence

ENV ATL_SSLENABLED 'False'

WORKDIR $CONFLUENCE_HOME

# Expose HTTP and Synchrony ports
EXPOSE 8090
EXPOSE 8091
EXPOSE 8443

CMD ["/entrypoint.py"]
ENTRYPOINT ["/sbin/tini", "--"]

RUN apk add --no-cache ca-certificates wget curl openssh bash procps openssl perl ttf-dejavu tini python3 py3-jinja2 tzdata tomcat-native

# Workaround for AdoptOpenJDK Alpine fontconfig bug
RUN ln -s /usr/lib/libfontconfig.so.1 /usr/lib/libfontconfig.so \
    && ln -s /lib/libuuid.so.1 /usr/lib/libuuid.so.1 \
    && ln -s /lib/libc.musl-x86_64.so.1 /usr/lib/libc.musl-x86_64.so.1
ENV LD_LIBRARY_PATH /usr/lib

ARG CONFLUENCE_VERSION=7.10.2
ARG DOWNLOAD_URL=https://product-downloads.atlassian.com/software/confluence/downloads/atlassian-confluence-${CONFLUENCE_VERSION}.tar.gz


ENV ATL_CERTIFICATE_PASSWORD 'changeit'
ENV ATL_CERTIFICATE_LOCATION '/opt/atlassian/confluence/keystore'
ENV ATL_CERTIFICATE_KEY_LOCATION  '/opt/atlassian/etc/certificate.key'
ENV ATL_CERTIFICATE_LOCATION '/opt/atlassian/etc/certificate.crt'

RUN addgroup -g ${RUN_GID} ${RUN_GROUP} \
    && adduser -u ${RUN_UID} -G ${RUN_GROUP} -h ${CONFLUENCE_HOME} -s /bin/bash -D ${RUN_USER} \
    \
    && mkdir -p                                     ${CONFLUENCE_INSTALL_DIR} \
    && curl -L --silent                             ${DOWNLOAD_URL} | tar -xz --strip-components=1 -C "${CONFLUENCE_INSTALL_DIR}" \
    && chmod -R "u=rwX,g=rX,o=rX"                   ${CONFLUENCE_INSTALL_DIR}/ \
    && chown -R root.                               ${CONFLUENCE_INSTALL_DIR}/ \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${CONFLUENCE_INSTALL_DIR}/logs \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${CONFLUENCE_INSTALL_DIR}/temp \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${CONFLUENCE_INSTALL_DIR}/work \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${CONFLUENCE_HOME} \
    && sed -i -e 's/-Xms\([0-9]\+[kmg]\) -Xmx\([0-9]\+[kmg]\)/-Xms\${JVM_MINIMUM_MEMORY:=\1} -Xmx\${JVM_MAXIMUM_MEMORY:=\2} -Dconfluence.home=\${CONFLUENCE_HOME}/g' ${CONFLUENCE_INSTALL_DIR}/bin/setenv.sh \
    && sed -i -e 's/-XX:ReservedCodeCacheSize=\([0-9]\+[kmg]\)/-XX:ReservedCodeCacheSize=\${JVM_RESERVED_CODE_CACHE_SIZE:=\1}/g' ${CONFLUENCE_INSTALL_DIR}/bin/setenv.sh \
    && sed -i -e 's/export CATALINA_OPTS/CATALINA_OPTS="\${CATALINA_OPTS} \${JVM_SUPPORT_RECOMMENDED_ARGS}"\n\nexport CATALINA_OPTS/g' ${CONFLUENCE_INSTALL_DIR}/bin/setenv.sh

VOLUME ["${CONFLUENCE_HOME}"]

COPY entrypoint.py \
     shared-components/image/entrypoint_helpers.py  /
COPY shared-components/support                      /opt/atlassian/support
COPY config/*                                       /opt/atlassian/etc/



RUN chmod +x /entrypoint.py
RUN chmod +x /entrypoint_helpers.py
