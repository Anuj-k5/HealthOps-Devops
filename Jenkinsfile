pipeline {
agent any

```
environment {
    DOCKER_IMAGE = "anujk5/healthops:latest"
    AWS_REGION = "ap-south-1"
    CLUSTER_NAME = "healthops-cluster"
}

stages {

    stage('Clone Repo') {
        steps {
            git branch: 'main',
            url: 'https://github.com/Anuj-k5/HealthOps-Devops.git'
        }
    }

    stage('Build Docker Image') {
        steps {
            sh 'docker build -t $DOCKER_IMAGE .'
        }
    }

    stage('Login DockerHub') {
        steps {
            withCredentials([usernamePassword(
                credentialsId: 'dockerhub-creds',
                usernameVariable: 'DOCKER_USER',
                passwordVariable: 'DOCKER_PASS'
            )]) {

                sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
            }
        }
    }

    stage('Push Docker Image') {
        steps {
            sh 'docker push $DOCKER_IMAGE'
        }
    }

    stage('Deploy To EKS') {
        steps {

            withCredentials([[
                $class: 'AmazonWebServicesCredentialsBinding',
                credentialsId: 'aws-creds'
            ]]) {

                sh '''
                aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
                kubectl apply -f k8s/
                kubectl rollout restart deployment healthops-app
                '''
            }
        }
    }
}
```

}
