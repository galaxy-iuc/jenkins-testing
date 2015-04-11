# Galaxy Tool testing in Jenkins

Jenkins scripts for testing Galaxy tool repositories

## Setup

1. You'll want to install [GitHub PR Builder Plugin](https://wiki.jenkins-ci.org/display/JENKINS/GitHub+pull+request+builder+plugin) and follow the setup instructions there.
2. Once you've done that, create a new project and point it at your GH Repo
3. Ensure that "Branch Specifier" is left blank.
4. Stick [test-repo.sh](test-repo.sh) in an execute-shell comamnd during the build phase
5. Publish JUnit reports from `reports/*.xml`
6. Publish HTML reports from `${WORKSPACE}/reports/${BUILD_NUMBER}/`, `index.html`
7. ...
8. Profit, from your ease-of-mind that all code of your tools are tested automatically.


## Known Issues

- Planemo doesn't currently support installing `tool_dependencies.xml`, so you'll need to install any binaries on your jenkins box *manually*.
