pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "anujk5/healthops"
        IMAGE_TAG = "${BUILD_NUMBER}"
        AWS_REGION = "ap-south-1"
        CLUSTER_NAME = "healthops-cluster"
        K8S_NAMESPACE = "healthops"
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend Smoke Tests') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                        docker run --rm \
                          -v "$PWD:/workspace" \
                          -w /workspace \
                          python:3.12-slim \
                          sh -lc "pip install --upgrade pip && pip install -r requirements.txt && python -m compileall app.py ci/smoke_test.py && python ci/smoke_test.py"
                        '''
                    } else {
                        powershell '''
                        docker run --rm `
                          -v "${pwd}:/workspace" `
                          -w /workspace `
                          python:3.12-slim `
                          sh -lc "pip install --upgrade pip && pip install -r requirements.txt && python -m compileall app.py ci/smoke_test.py && python ci/smoke_test.py"
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker build -t $DOCKER_IMAGE:$IMAGE_TAG -t $DOCKER_IMAGE:latest .'
                    } else {
                        powershell 'docker build -t ${env:DOCKER_IMAGE}:${env:IMAGE_TAG} -t ${env:DOCKER_IMAGE}:latest .'
                    }
                }
            }
        }

        stage('Login DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    script {
                        if (isUnix()) {
                            sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                        } else {
                            powershell '$env:DOCKER_PASS | docker login -u $env:DOCKER_USER --password-stdin'
                        }
                    }
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                        docker push $DOCKER_IMAGE:$IMAGE_TAG
                        docker push $DOCKER_IMAGE:latest
                        '''
                    } else {
                        powershell '''
                        docker push ${env:DOCKER_IMAGE}:${env:IMAGE_TAG}
                        docker push ${env:DOCKER_IMAGE}:latest
                        '''
                    }
                }
            }
        }

        stage('Deploy To EKS') {
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-creds'],
                    string(credentialsId: 'healthops-secret-key', variable: 'APP_SECRET_KEY'),
                    string(credentialsId: 'healthops-api-token', variable: 'API_TOKEN'),
                    string(credentialsId: 'healthops-postgres-db', variable: 'POSTGRES_DB'),
                    string(credentialsId: 'healthops-postgres-user', variable: 'POSTGRES_USER'),
                    string(credentialsId: 'healthops-postgres-password', variable: 'POSTGRES_PASSWORD'),
                    string(credentialsId: 'grafana-admin-user', variable: 'GRAFANA_ADMIN_USER'),
                    string(credentialsId: 'grafana-admin-password', variable: 'GRAFANA_ADMIN_PASSWORD')
                ]) {
                    script {
                        if (isUnix()) {
                            sh '''
                            aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

                            DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@healthops-postgres.${K8S_NAMESPACE}.svc.cluster.local:5432/${POSTGRES_DB}"

                            kubectl apply -f k8s/namespace.yaml
                            kubectl create secret generic healthops-secrets \
                              --namespace $K8S_NAMESPACE \
                              --from-literal=SECRET_KEY="$APP_SECRET_KEY" \
                              --from-literal=API_TOKEN="$API_TOKEN" \
                              --from-literal=POSTGRES_DB="$POSTGRES_DB" \
                              --from-literal=POSTGRES_USER="$POSTGRES_USER" \
                              --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
                              --from-literal=DATABASE_URL="$DATABASE_URL" \
                              --from-literal=GRAFANA_ADMIN_USER="$GRAFANA_ADMIN_USER" \
                              --from-literal=GRAFANA_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" \
                              --dry-run=client -o yaml | kubectl apply -f -

                            kubectl apply -f k8s/configmap.yaml
                            kubectl apply -f k8s/postgres.yaml
                            kubectl rollout status deployment/healthops-postgres -n $K8S_NAMESPACE --timeout=180s

                            kubectl apply -f k8s/deployment.yaml
                            kubectl apply -f k8s/service.yaml
                            kubectl set image deployment/healthops-backend healthops-backend=$DOCKER_IMAGE:$IMAGE_TAG -n $K8S_NAMESPACE
                            kubectl rollout status deployment/healthops-backend -n $K8S_NAMESPACE --timeout=180s

                            kubectl apply -f monitoring/
                            kubectl rollout status deployment/prometheus -n $K8S_NAMESPACE --timeout=180s
                            kubectl rollout status deployment/grafana -n $K8S_NAMESPACE --timeout=180s

                            kubectl get svc -n $K8S_NAMESPACE
                            '''
                        } else {
                            powershell '''
                            aws eks update-kubeconfig --region $env:AWS_REGION --name $env:CLUSTER_NAME

                            $databaseUrl = "postgresql+psycopg://$($env:POSTGRES_USER):$($env:POSTGRES_PASSWORD)@healthops-postgres.$($env:K8S_NAMESPACE).svc.cluster.local:5432/$($env:POSTGRES_DB)"

                            kubectl apply -f k8s/namespace.yaml
                            kubectl create secret generic healthops-secrets `
                              --namespace $env:K8S_NAMESPACE `
                              --from-literal=SECRET_KEY="$env:APP_SECRET_KEY" `
                              --from-literal=API_TOKEN="$env:API_TOKEN" `
                              --from-literal=POSTGRES_DB="$env:POSTGRES_DB" `
                              --from-literal=POSTGRES_USER="$env:POSTGRES_USER" `
                              --from-literal=POSTGRES_PASSWORD="$env:POSTGRES_PASSWORD" `
                              --from-literal=DATABASE_URL="$databaseUrl" `
                              --from-literal=GRAFANA_ADMIN_USER="$env:GRAFANA_ADMIN_USER" `
                              --from-literal=GRAFANA_ADMIN_PASSWORD="$env:GRAFANA_ADMIN_PASSWORD" `
                              --dry-run=client -o yaml | kubectl apply -f -

                            kubectl apply -f k8s/configmap.yaml
                            kubectl apply -f k8s/postgres.yaml
                            kubectl rollout status deployment/healthops-postgres -n $env:K8S_NAMESPACE --timeout=180s

                            kubectl apply -f k8s/deployment.yaml
                            kubectl apply -f k8s/service.yaml
                            kubectl set image deployment/healthops-backend healthops-backend=$env:DOCKER_IMAGE`:$env:IMAGE_TAG -n $env:K8S_NAMESPACE
                            kubectl rollout status deployment/healthops-backend -n $env:K8S_NAMESPACE --timeout=180s

                            kubectl apply -f monitoring/
                            kubectl rollout status deployment/prometheus -n $env:K8S_NAMESPACE --timeout=180s
                            kubectl rollout status deployment/grafana -n $env:K8S_NAMESPACE --timeout=180s

                            kubectl get svc -n $env:K8S_NAMESPACE
                            '''
                        }
                    }
                }
            }
        }
    }
}
