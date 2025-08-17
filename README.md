# Flask Comments API

[![Deploy Status](https://img.shields.io/badge/deploy-success-green.svg)](https://github.com)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Descripción

API RESTful desarrollada con Flask para la gestión de comentarios, incluyendo integración con APIs externas, sistema de validación robusto, rate limiting y despliegue automatizado en Google Cloud Run.

### Características Principales

- **Seguridad robusta**: Rate limiting, validación de entrada, sanitización XSS
-  **Integración externa**: API de clima (OpenWeatherMap)
-  **Testing completo**: Suite de pruebas unitarias y de integración
-  **Containerización**: Docker con multi-stage builds optimizados
-  **CI/CD**: Despliegue automatizado con GitHub Actions
-  **Monitoreo**: Logging estructurado y health checks
-  **Escalabilidad**: Configuración lista para producción

##  Arquitectura

flask-comments-api/
├── app.py                     # Aplicación principal
├── config.py                  # Configuraciones por entorno
├── requirements.txt           # Dependencias Python
├── Dockerfile                 # Configuración Docker
├── docker-compose.yml         # Orquestación local
├── middleware/
│   ├── init.py
│   └── security.py           # Rate limiting y validación
├── utils/
│   ├── init.py
│   ├── validators.py         # Validación de entrada
│   └── logger.py            # Sistema de logging
├── tests/
│   └── test_app.py          # Suite de pruebas
└── .github/workflows/
└── deploy.yaml          # Pipeline CI/CD

##  Inicio Rápido

### Prerequisitos
- Python 3.11+
- Docker (opcional)
- Cuenta de Google Cloud (para despliegue)

### Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/flask-comments-api.git
cd flask-comments-api

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export FLASK_ENV=development
export SECRET_KEY=tu-secret-key-aqui
export WEATHER_API_KEY=tu-api-key-openweather

# Ejecutar aplicación
python app.py

Con Docker
bash# Desarrollo
docker-compose --profile dev up flask-dev

# Producción
docker-compose up flask-app
API Endpoints
Comentarios
GET /comments
Obtiene todos los comentarios
Respuesta:
json{
  "comments": [...],
  "total": 2,
  "timestamp": "2024-01-15T10:30:00"
}
POST /comments
Crea un nuevo comentario
Cuerpo de la petición:
json{
  "author": "Juan Pérez",
  "comment": "Este es un comentario excelente"
}
GET /comments/{id}
Obtiene un comentario específico
DELETE /comments/{id}
Elimina un comentario específico
Otros Endpoints

GET / - Información general de la API
GET /health - Health check para monitoreo
GET /weather/{ciudad} - Información del clima
GET /api-demo - Demostración de consumo API externa

Seguridad
Rate Limiting

Endpoint principal: 200 req/hora
Comentarios GET: 150 req/hora
Comentarios POST: 50 req/hora
Weather API: 60 req/hora

Validación de Entrada

Sanitización XSS automática
Validación de longitud de campos
Detección de contenido malicioso
Escape de caracteres especiales

Headers de Seguridad
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Testing
bash# Ejecutar todas las pruebas
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=. --cov-report=html

# Linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Formateo de código
black . --check
isort . --check-only

 Despliegue
Variables de Entorno Requeridas en GitHub:

GCP_PROJECT_ID: ID del proyecto en Google Cloud
GCP_SA_KEY: Clave JSON de la cuenta de servicio

Pipeline Automatizado:

Test: Ejecuta pruebas unitarias y linting
Security: Escaneo de vulnerabilidades con Bandit/Safety
Build: Construcción de imagen Docker
Deploy: Despliegue en Cloud Run
Verify: Verificación post-despliegue

 Monitoreo y Logs
Logging Estructurado
json{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "message": "Request processed successfully",
  "module": "app",
  "extra_data": {
    "method": "POST",
    "endpoint": "/comments",
    "status_code": 201,
    "response_time_ms": 45
  }
}
Health Checks

GET /health retorna estado de la aplicación
Docker health check cada 30 segundos
Verificación de dependencias externas

 Contribuir

Fork del repositorio
Crear rama feature (git checkout -b feature/nueva-funcionalidad)
Commit cambios (git commit -am 'Agregar nueva funcionalidad')
Push a la rama (git push origin feature/nueva-funcionalidad)
Crear Pull Request

 Changelog
v1.0.0 (2024-01-15)

Implementación inicial de API de comentarios
Sistema de seguridad robusto con rate limiting
Integración con OpenWeatherMap API
Containerización con Docker
Pipeline CI/CD con GitHub Actions
Sistema de logging y monitoreo

 Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.
Equipo

Desarrollador Principal: Tu Nombre
Universidad: UTEQ
Curso: DevOps y CI/CD