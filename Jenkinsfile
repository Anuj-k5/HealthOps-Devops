pipeline {
    agent any

    environment {
        IMAGE_NAME = "healthops-app"
        REGISTRY = "docker.io/akshata234"
    }

    stages {

        stage('Clone Repo') {
            steps {
                git url: 'https://github.com/Akshata-del1531/healthops-app.git', branch: 'main'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t %REGISTRY%/%IMAGE_NAME%:latest ."
            }
        }

        stage('Login to DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat "echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                bat "docker push %REGISTRY%/%IMAGE_NAME%:latest"
            }
        }

        stage('Deploy to AWS EKS') {
            steps {
                withCredentials([aws(credentialsId: 'aws-credentials', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    bat """
                    aws eks update-kubeconfig --region ap-south-1 --name healthops-cluster
                    kubectl apply -f k8s/
                    """
                }
            }
        }
    }
}