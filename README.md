# HealthOps-Devops

## Project Overview
HealthOps-Devops is a healthcare monitoring and management application integrated with DevOps practices for automated build, testing, deployment, and scalability.  
The project uses CI/CD pipelines with Jenkins, containerization using Docker, and orchestration through Kubernetes.

---

## Team Collaborators
- Akshata M
- Team Member 2
- Team Member 3
- Team Member 4

---

## Technologies Used
- Python
- Flask
- Docker
- Jenkins
- Kubernetes
- GitHub
- HTML
- CSS
- YAML

---

## Project Architecture

The project follows a DevOps workflow:

1. Developer pushes code to GitHub
2. Jenkins pipeline gets triggered
3. Docker image is created
4. Kubernetes deploys the application
5. Application runs in containerized environment

---

## Folder Structure

```text
HealthOps-Devops/
│
├── database/               # Database related files
├── healthops-app-main/    # Main application files
├── instance/              # Instance configurations
├── k8s/                   # Kubernetes YAML deployment files
├── static/                # CSS, JavaScript, images
├── templates/             # HTML template files
│
├── .dockerignore          # Docker ignore file
├── Dockerfile             # Docker image build instructions
├── Jenkinsfile            # Jenkins CI/CD pipeline
├── app.py                 # Main Flask application
├── nodegroup.yaml         # Kubernetes node configuration
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## Features
- Automated CI/CD Pipeline
- Docker Containerization
- Kubernetes Deployment
- Healthcare Monitoring System
- Scalable Architecture
- GitHub Integration
- Jenkins Automation

---

## Prerequisites

Before running the project, install:

- Python 3.x
- Docker
- Jenkins
- Kubernetes
- Git
- kubectl

---

## Installation Steps

### Clone the Repository

```bash
git clone https://github.com/your-repository-name.git
```

### Move to Project Directory

```bash
cd HealthOps-Devops
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
python app.py
```

The application will start on:

```text
http://localhost:5000
```

---

## Docker Setup

### Build Docker Image

```bash
docker build -t healthops-app .
```

### Run Docker Container

```bash
docker run -p 5000:5000 healthops-app
```

---

## Jenkins CI/CD Pipeline

The Jenkins pipeline performs:

- Source code checkout
- Dependency installation
- Docker image build
- Docker container deployment
- Kubernetes deployment

---

## Kubernetes Deployment

Apply Kubernetes configuration files:

```bash
kubectl apply -f k8s/
```

Check running pods:

```bash
kubectl get pods
```

Check services:

```bash
kubectl get services
```

---

## Future Enhancements
- AI-based healthcare prediction
- Real-time monitoring dashboard
- Cloud deployment
- Security improvements
- Advanced analytics integration

---

## Conclusion

This project demonstrates the integration of healthcare applications with modern DevOps practices using Docker, Jenkins, and Kubernetes.  
The automated CI/CD pipeline improves deployment speed, scalability, and reliability while reducing manual intervention.

---

## License

This project is developed for educational and learning purposes.
"test" 
