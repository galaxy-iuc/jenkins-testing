# Galaxy Tool testing in Jenkins

Jenkins scripts for testing Galaxy tool repositories

## Setup

1. (Optional) Build a jenkins image (based on https://github.com/jenkinsci/docker) using the supplied Dockerfile.
2. Configure security and add a new free-style project in jenkins.
3. Add your tool-repo to jenkins (Bitbucket and Github work fine.)
4. Make sure that you have .shed.yml files for the tools you want to test.
   Add an additional section that specifies your test targets in the .shed.yml.
3. Modify jenkins.sh to suit your needs and run it in your new project. 
4. Download jenkins.sh and execute it in your project.
4. Publish JUnit reports from `reports/*.xml`
5. Publish HTML reports from `${WORKSPACE}/reports/${BUILD_NUMBER}/`, `index.html`
6. Profit, from your ease-of-mind that all code of your tools are tested automatically.


## Known Issues


## TODO

- Convert to `build.xml` or similar (something easily `wget/curl`-able)

# Galaxy Repository Pushing from GitHub to the ToolShed

