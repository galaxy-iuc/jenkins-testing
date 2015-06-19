# Galaxy Tool testing in Jenkins

Jenkins scripts for testing Galaxy tool repositories

## Setup

1. You'll want to install [GitHub PR Builder Plugin](https://wiki.jenkins-ci.org/display/JENKINS/GitHub+pull+request+builder+plugin) and follow the setup instructions there.
2. Once you've done that, create a new project and point it at your GH Repo
3. Ensure that "Branch Specifier" is left blank.
4. Stick [test-repo.py](test-repo.py) in an execute-shell command during the build phase
5. Publish JUnit reports from `reports/*.xml`
6. Publish HTML reports from `${WORKSPACE}/reports/${BUILD_NUMBER}/`, `index.html`
7. ...
8. Profit, from your ease-of-mind that all code of your tools are tested automatically.


## Known Issues

- Planemo doesn't currently support installing `tool_dependencies.xml`, so you'll need to install any binaries on your jenkins box *manually*.

## TODO

- Convert to `build.xml` or similar (something easily `wget/curl`-able)

# Galaxy Repository Pushing from GitHub to the ToolShed

We additionally provide a build script for pushing to the TS.

## Setup

1. Create a new project and point it at your GH Repo
2. Ensure that "Branch Specifier" is set to master (because you only allow perfect, working code into master)
3. Stick [push-repo.sh](push-repo.sh) in an execute-shell command during the build phase
4. Publish HTML reports from `${WORKSPACE}/reports/${BUILD_NUMBER}/`, `index.html`
5. The IUC currently recommends doing the push on a `@daily` basis, rater than on every push.

## Known Issues

- Reports are hard to read
- Has to run twice because planemo isn't aware of dependencies locally [planemo#71](https://github.com/galaxyproject/planemo/issues/71)
