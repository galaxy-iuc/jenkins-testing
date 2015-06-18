FROM jenkins
MAINTAINER Marius van den Beek <victor@docker.com>

# if we want to install via apt
USER root
RUN apt-get update && apt-get install -y parallel
USER jenkins
