FROM jenkins
# if we want to install via apt
# we're getting the toolshed dependencies and samtools
USER root
RUN apt-get -qq update && apt-get install --no-install-recommends -y apt-transport-https software-properties-common && \
    apt-get install --no-install-recommends -y autoconf automake build-essential gfortran cmake \
    git-core libatlas-base-dev libblas-dev liblapack-dev openssl samtools\
    openjdk-7-jre-headless python-dev libxml2-utils\
    python-virtualenv zlib1g-dev libyaml-dev subversion python-dev pkg-config && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


#Add tini to surveil planemo spawning zombies
ENV TINI_VERSION v0.5.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

USER jenkins
ENTRYPOINT ["/tini", "--", "/usr/local/bin/jenkins.sh"]  
