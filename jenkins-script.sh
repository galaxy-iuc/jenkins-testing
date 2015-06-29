#!/bin/sh
# Pass local or testttolshed as arguments

TARGET="${1^^}"

echo "Setting up planemo, if not installed"
if [ ! -f "get-pip.py" ]
then
    echo "Installing pip, virtualenv"
    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
	python get-pip.py --user
    export PATH=~/.local/bin:$PATH
    pip install --user virtualenv
    virtualenv venv --no-site-packages
fi

export PATH=~/.local/bin:$PATH
. venv/bin/activate
 
pip install --upgrade planemo
planemo --version

echo "Setting up jenkins test script and retrieving API keys"

if [ ! -d "jenkins-testing/" ]
then
	git clone https://github.com/mvdbeek/jenkins-testing.git
fi

if [ ! -d "lab-coding/" ]
then
    hg clone https://mvdbeek:${bitbucket_pw}@bitbucket.org/mvdbeek/lab-coding
fi

cd lab-coding
hg pull -u https://mvdbeek:${bitbucket_pw}@bitbucket.org/mvdbeek/lab-coding
cd ../

cd jenkins-testing
git pull && git checkout

echo "Starting job"

#Local toolshed test

if [ "$TARGET" == "LOCAL" ];
then
    python ./test-repo.py shed_test --tool_dirs ${WORKSPACE}/packages ${WORKSPACE}/tools \
       --report_dir ${WORKSPACE}/reports --build_number ${BUILD_NUMBER} --cores 10 \
       --api_keys ${WORKSPACE}/lab-coding/api_keys/api_keys.yaml  --shed_target https://lbcd41.snv.jussieu.fr/toolshed/

elif [ "$TARGET" == "TESTTOOLSHED" ];
then
      python ./test-repo.py shed_test --tool_dirs ${WORKSPACE}/packages ${WORKSPACE}/tools \
       --report_dir ${WORKSPACE}/reports --build_number ${BUILD_NUMBER} --cores 10 \
       --api_keys ${WORKSPACE}/lab-coding/api_keys/api_keys.yaml  --shed_target testtoolshed
else
      echo "Choose local or testtoolshed"
fi

