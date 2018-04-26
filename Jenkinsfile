#!/usr/bin/groovy

// Jenkins configuration
def defaultNode = "docker"

node(defaultNode)
{
    // Build the Docker image for this service in order to run the tests
    stage("Build")
    {
        sh "docker build -t ultimaker/libcharon:tests ."
    }
}
