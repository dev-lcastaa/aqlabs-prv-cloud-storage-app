pipeline {
    agent { label 'node-d-worker' }

    parameters {
        booleanParam(name: 'NO_CACHE_REBUILD', defaultValue: false, description: 'Rebuild Docker images with --no-cache')
        booleanParam(name: 'PULL_BASE_IMAGES', defaultValue: true, description: 'Pull latest base images during build')
        booleanParam(name: 'RUN_FRONTEND_QUALITY_GATE', defaultValue: true, description: 'Run frontend lint/build before container build')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_PROJECT_NAME = 'aqlabs-object-store'
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
    }

    stages {

        stage('Checkout Source') {
            steps {
                echo 'Checking out source...'
                checkout scm
            }
        }

        stage('Validate Tooling') {
            steps {
                echo 'Validating Docker and Compose availability...'
                sh '''
                docker --version
                docker compose version
                docker compose config > /dev/null
                '''
            }
        }

        stage('Frontend Quality Gate') {
            when {
                expression { return params.RUN_FRONTEND_QUALITY_GATE }
            }
            steps {
                echo 'Running frontend lint and build...'
                dir('frontend') {
                    sh '''
                    npm ci
                    npm run lint
                    npm run build
                    '''
                }
            }
        }

        stage('Build Container Images') {
            steps {
                echo 'Building backend and frontend images...'
                script {
                    def buildFlags = ''
                    if (params.NO_CACHE_REBUILD) {
                        buildFlags += ' --no-cache'
                    }
                    if (params.PULL_BASE_IMAGES) {
                        buildFlags += ' --pull'
                    }

                    sh """
                    docker compose build${buildFlags}
                    """
                }
            }
        }

        stage('Deploy Stack') {
            steps {
                echo 'Deploying stack with docker compose...'
                sh '''
                docker compose up -d --build --remove-orphans
                docker compose ps
                '''
            }
        }

        stage('Smoke Tests') {
            steps {
                echo 'Running smoke tests against backend and frontend...'
                sh '''
                set +e

                for i in $(seq 1 30); do
                  curl -fsS http://localhost:8000/health >/dev/null && break
                  sleep 2
                done

                for i in $(seq 1 30); do
                  curl -fsS http://localhost:5173 >/dev/null && break
                  sleep 2
                done

                curl -fsS http://localhost:8000/health
                curl -fsS http://localhost:5173 >/dev/null

                set -e
                '''
            }
        }
    }

    post {

        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Collecting compose diagnostics...'
            sh '''
            docker compose ps || true
            docker compose logs --no-color --tail=200 || true
            '''
        }

        always {
            echo 'Post-build compose status:'
            sh '''
            docker compose ps || true
            '''
        }
    }
}
