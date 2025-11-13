# 🚀 Análisis de Feedback de GitHub

Como desarrollador, ¿quieres recibir feedback pero no sabes por dónde empezar con tu retrospectiva de fin de año? Una herramienta CLI que analiza **tu actividad** en GitHub y genera automáticamente informes perspicaces. Compatible con GitHub.com y GitHub Enterprise, con capacidades de revisión automatizada basadas en LLM.

Español | [한국어](../README.md) | [English](README_EN.md) | [简体中文](README_ZH.md) | [日本語](README_JA.md)

## ✨ Características Principales

- 📊 **Análisis de Actividad Personal**: Agrega y analiza **tus** commits, issues y actividad de revisión en un repositorio específico por período
- 🤖 **Feedback Basado en LLM**: Análisis detallado de tus mensajes de commit, títulos de PR, tono de revisión y calidad de issues
- 🎯 **Informe Retrospectivo Integrado**: Proporciona insights integrales junto con métricas de actividad personal
- 🏆 **Visualización de Logros**: Genera automáticamente premios y destacados basados en tus contribuciones
- 💡 **Descubrimiento de Repositorios**: Lista repositorios accesibles y sugiere los activos
- 🎨 **Modo Interactivo**: Interfaz amigable para selección directa de repositorios

## 📋 Requisitos Previos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/) o su gestor de paquetes preferido
- GitHub Personal Access Token
  - Repositorios privados: permiso `repo`
  - Repositorios públicos: permiso `public_repo`
- Endpoint de API LLM (formato compatible con OpenAI)

<details>
<summary><b>🔑 Generar GitHub Personal Access Token</b></summary>

Necesita un GitHub Personal Access Token (PAT) para usar esta herramienta.

### Cómo Generar

1. **Acceder a Configuración de GitHub**
   - Ir a [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
   - O: Perfil de GitHub → Settings → Developer settings → Personal access tokens

2. **Generar Nuevo Token**
   - Hacer clic en "Generate new token" → "Generate new token (classic)"
   - Note: Ingrese el propósito del token (ej: "GitHub Feedback Analysis")
   - Expiration: Establecer período de expiración (recomendado: 90 días o Custom)

3. **Seleccionar Permisos**
   - **Solo repositorios públicos**: Marcar `public_repo`
   - **Incluyendo repositorios privados**: Marcar todo `repo`
   - No se requieren otros permisos

4. **Generar y Copiar Token**
   - Hacer clic en "Generate token"
   - Copiar el token generado (comienza con ghp_) y guardarlo de forma segura
   - ⚠️ **Importante**: No podrá ver este token nuevamente después de salir de la página

5. **Usar Token**
   - Ingresar el token copiado al ejecutar `gfa init`

### Usar Fine-grained Personal Access Token (Opcional)

Para usar los tokens de grano fino más nuevos:
1. Ir a [Personal access tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Repository access: Seleccionar repositorios a analizar
3. Configurar Permisos:
   - **Contents**: Read-only (requerido)
   - **Metadata**: Read-only (seleccionado automáticamente)
   - **Pull requests**: Read-only (requerido)
   - **Issues**: Read-only (requerido)

### Para Usuarios de GitHub Enterprise

Si está usando GitHub Enterprise en su organización:
1. **Acceder a la Página de Tokens del Servidor Enterprise**
   - `https://github.your-company.com/settings/tokens` (reemplazar con el dominio de su empresa)
   - O: Perfil → Settings → Developer settings → Personal access tokens

2. **La Configuración de Permisos es la Misma**
   - Repositorios privados: permiso `repo`
   - Repositorios públicos: permiso `public_repo`

3. **Especificar Host Enterprise Durante la Configuración Inicial**
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **Contactar al Administrador**
   - La generación de PAT puede estar restringida en algunos entornos Enterprise
   - Contacte a su administrador de GitHub si encuentra problemas

### Referencias

- [Documentación de GitHub: Gestión de Personal Access Tokens](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Documentación de GitHub: Fine-grained PAT](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [Documentación de GitHub Enterprise Server](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 Instalación

```bash
# Copiar el repositorio
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# Crear y activar entorno virtual
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar paquete
uv pip install -e .
```

## 🚀 Inicio Rápido

### 1️⃣ Inicializar Configuración

```bash
gfa init
```

Cuando se le solicite, ingrese la siguiente información:
- GitHub Personal Access Token (almacenado de forma segura en el llavero del sistema)
- Endpoint LLM (ej: `http://localhost:8000/v1/chat/completions`)
- Modelo LLM (ej: `gpt-4`)
- Host de GitHub Enterprise (opcional, solo si no usa github.com)

### 2️⃣ Analizar Actividad Personal

```bash
gfa feedback
```

Puede elegir de una lista de repositorios recomendados o ingresar uno directamente para analizar **tu actividad**.

Después de completar el análisis, se generan los siguientes archivos en el directorio `reports/`:
- `metrics.json` - Datos de análisis
- `report.md` - Informe en Markdown
- `report.html` - Informe HTML (con gráficos de visualización)
- `charts/` - Archivos de gráficos SVG
- `prompts/` - Archivos de prompts LLM

### 3️⃣ Ver Resultados

```bash
cat reports/report.md
```

## 📚 Referencia de Comandos

<details>
<summary><b>🎯 `gfa init` - Configuración Inicial</b></summary>

Almacena información de acceso a GitHub y configuración de LLM.

#### Uso Básico (Interactivo)

```bash
gfa init
```

#### Ejemplo: GitHub.com + LLM Local

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### Ejemplo: GitHub Enterprise

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.company.com \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4
```

#### Opciones

| Opción | Descripción | Requerido | Predeterminado |
|--------|-------------|-----------|----------------|
| `--pat` | GitHub Personal Access Token | ✅ | - |
| `--llm-endpoint` | Endpoint de API LLM | ✅ | - |
| `--llm-model` | Identificador del modelo LLM | ✅ | - |
| `--months` | Período de análisis predeterminado (meses) | ❌ | 12 |
| `--enterprise-host` | Host de GitHub Enterprise | ❌ | github.com |

</details>

<details>
<summary><b>📊 gfa feedback - Análisis de Actividad Personal</b></summary>

Analiza **tu actividad** en un repositorio específico y genera informes de feedback detallados.

> **Importante**: Este comando solo analiza la actividad personal del usuario autenticado (propietario del PAT). No analiza todo el repositorio, sino únicamente **tus** commits, PRs, revisiones e issues.

#### Uso Básico

```bash
gfa feedback --repo owner/repo-name
```

#### Modo Interactivo

Seleccione un repositorio de la lista recomendada sin especificarlo directamente.

```bash
gfa feedback --interactive
```

O

```bash
gfa feedback  # Ejecutar sin la opción --repo
```

#### Ejemplos

```bash
# Analizar repositorio público donde he contribuido
gfa feedback --repo torvalds/linux

# Analizar mi repositorio personal
gfa feedback --repo myusername/my-private-repo

# Analizar repositorio de organización donde he contribuido
gfa feedback --repo microsoft/vscode

# Modo interactivo para selección de repositorio
gfa feedback --interactive
```

#### Opciones

| Opción | Descripción | Requerido | Predeterminado |
|--------|-------------|-----------|----------------|
| `--repo`, `-r` | Repositorio (owner/name) | ❌ | - |
| `--output`, `-o` | Directorio de salida | ❌ | reports |
| `--interactive`, `-i` | Selección interactiva de repositorio | ❌ | false |

#### Informes Generados

Después de completar el análisis, se crean los siguientes archivos en el directorio `reports/`:

```
reports/
├── metrics.json              # Datos de análisis
├── report.md                 # Informe en Markdown
├── report.html               # Informe HTML (con gráficos de visualización)
├── charts/                   # Gráficos de visualización
│   ├── quality.svg          # Gráfico de métricas de calidad
│   ├── activity.svg         # Gráfico de métricas de actividad
│   └── ...                  # Otros gráficos específicos del dominio
└── prompts/
    ├── commit_feedback.txt   # Feedback sobre calidad de mensajes de commit
    ├── pr_feedback.txt       # Feedback sobre títulos de PR
    ├── review_feedback.txt   # Feedback sobre tono de revisión
    └── issue_feedback.txt    # Feedback sobre calidad de issues
```

#### Contenido del Análisis

- ✅ **Agregación de Actividad**: Cuenta tus commits, PRs, revisiones e issues
- 🎯 **Análisis de Calidad**: Calidad de tus mensajes de commit, títulos de PR, tono de revisión y descripción de issues
- 🏆 **Premios**: Premios automáticos basados en tus contribuciones
- 📈 **Tendencias**: Tendencias de tu actividad mensual y análisis de velocidad
- 🤝 **Análisis de Colaboración**: Red de colaboradores que han trabajado contigo
- 💻 **Análisis de Stack Tecnológico**: Lenguajes y tecnologías en los archivos que has trabajado

</details>

<details>
<summary><b>⚙️ `gfa config` - Gestión de Configuración</b></summary>

Ver o modificar la configuración.

#### `gfa config show` - Ver Configuración

Ver la configuración actualmente almacenada.

```bash
gfa config show
```

**Ejemplo de Salida:**

```
┌─────────────────────────────────────┐
│ GitHub Feedback Configuration       │
├─────────────┬───────────────────────┤
│ Section     │ Values                │
├─────────────┼───────────────────────┤
│ auth        │ pat = <set>           │
├─────────────┼───────────────────────┤
│ server      │ api_url = https://... │
│             │ web_url = https://... │
├─────────────┼───────────────────────┤
│ llm         │ endpoint = http://... │
│             │ model = gpt-4         │
└─────────────┴───────────────────────┘
```

> **Nota:** El comando `gfa show-config` está obsoleto y ha sido reemplazado por `gfa config show`.

#### `gfa config set` - Establecer Valores de Configuración

Modifica valores de configuración individuales.

```bash
gfa config set <key> <value>
```

**Ejemplos:**

```bash
# Cambiar modelo LLM
gfa config set llm.model gpt-4

# Cambiar endpoint LLM
gfa config set llm.endpoint http://localhost:8000/v1/chat/completions

# Cambiar período de análisis predeterminado
gfa config set defaults.months 6
```

#### `gfa config get` - Obtener Valores de Configuración

Recupera valores de configuración específicos.

```bash
gfa config get <key>
```

**Ejemplos:**

```bash
# Verificar modelo LLM
gfa config get llm.model

# Verificar período de análisis predeterminado
gfa config get defaults.months
```

</details>

<details>
<summary><b>🔍 `gfa list-repos` - Listar Repositorios</b></summary>

Lista los repositorios accesibles.

```bash
gfa list-repos
```

#### Ejemplos

```bash
# Listar repositorios (predeterminado: 20 actualizados recientemente)
gfa list-repos

# Cambiar criterio de ordenamiento
gfa list-repos --sort stars --limit 10

# Filtrar por organización específica
gfa list-repos --org myorganization

# Ordenar por fecha de creación
gfa list-repos --sort created --limit 50
```

#### Opciones

| Opción | Descripción | Predeterminado |
|--------|-------------|----------------|
| `--sort`, `-s` | Criterio de ordenamiento (updated, created, pushed, full_name) | updated |
| `--limit`, `-l` | Número máximo a mostrar | 20 |
| `--org`, `-o` | Filtrar por nombre de organización | - |

</details>

<details>
<summary><b>💡 `gfa suggest-repos` - Sugerencias de Repositorios</b></summary>

Sugiere repositorios activos adecuados para análisis.

```bash
gfa suggest-repos
```

Selecciona automáticamente repositorios con actividad reciente. Considera de manera integral estrellas, forks, issues y actualizaciones recientes.

#### Ejemplos

```bash
# Sugerencias predeterminadas (dentro de los últimos 90 días, 10 repositorios)
gfa suggest-repos

# Sugerir 5 repositorios activos en los últimos 30 días
gfa suggest-repos --limit 5 --days 30

# Ordenar por estrellas
gfa suggest-repos --sort stars

# Ordenar por puntuación de actividad (evaluación integral)
gfa suggest-repos --sort activity
```

#### Opciones

| Opción | Descripción | Predeterminado |
|--------|-------------|----------------|
| `--limit`, `-l` | Número máximo de sugerencias | 10 |
| `--days`, `-d` | Período de actividad reciente (días) | 90 |
| `--sort`, `-s` | Criterio de ordenamiento (updated, stars, activity) | activity |

</details>

<details>
<summary><b>📁 Archivo de Configuración</b></summary>

La configuración se almacena en `~/.config/github_feedback/config.toml` y se crea automáticamente al ejecutar `gfa init`.

### Ejemplo de Archivo de Configuración

```toml
[version]
version = "1.0.0"

[auth]
# El PAT se almacena de forma segura en el llavero del sistema (no en este archivo)

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"
timeout = 60
max_files_in_prompt = 10
max_retries = 3

[defaults]
months = 12
```

### Edición Manual de Configuración

Si es necesario, puede editar el archivo de configuración directamente o usar los comandos `gfa config`:

```bash
# Método 1: Usar comandos config (recomendado)
gfa config set llm.model gpt-4
gfa config show

# Método 2: Edición directa
nano ~/.config/github_feedback/config.toml
```

</details>

<details>
<summary><b>📊 Estructura de Archivos Generados</b></summary>

### Salida de `gfa feedback`

```
reports/
├── metrics.json              # 📈 Datos de análisis de actividad personal (JSON)
├── report.md                 # 📄 Informe en Markdown
├── report.html               # 🎨 Informe HTML (con gráficos de visualización)
├── charts/                   # 📊 Gráficos de visualización (SVG)
│   ├── quality.svg          # Gráfico de métricas de calidad
│   ├── activity.svg         # Gráfico de métricas de actividad
│   ├── engagement.svg       # Gráfico de participación
│   └── ...                  # Otros gráficos específicos del dominio
└── prompts/
    ├── commit_feedback.txt   # 💬 Análisis de calidad de mensajes de commit
    ├── pr_feedback.txt       # 🔀 Análisis de títulos de PR
    ├── review_feedback.txt   # 👀 Análisis de tono de revisión
    └── issue_feedback.txt    # 🐛 Análisis de calidad de issues
```

</details>

<details>
<summary><b>💡 Ejemplos de Uso</b></summary>

### Ejemplo 1: Inicio Rápido - Modo Interactivo

```bash
# 1. Configuración (solo la primera vez)
gfa init

# 2. Obtener sugerencias de repositorios
gfa suggest-repos

# 3. Analizar tu actividad en modo interactivo
gfa feedback --interactive

# 4. Ver informe
cat reports/report.md
```

### Ejemplo 2: Análisis de Contribuciones a Código Abierto

```bash
# 1. Configuración (solo la primera vez)
gfa init

# 2. Analizar tu actividad de contribución a proyecto de código abierto
gfa feedback --repo facebook/react

# 3. Ver informe (solo muestra tu actividad de contribución)
cat reports/report.md
```

### Ejemplo 3: Retrospectiva de Proyecto Personal

```bash
# Verificar lista de mis repositorios
gfa list-repos --sort updated --limit 10

# Analizar mi actividad en mi proyecto
gfa feedback --repo myname/my-awesome-project

# Ver informe
cat reports/report.md
```

### Ejemplo 4: Revisión de Tu Rendimiento en Proyecto de Equipo

```bash
# Verificar lista de repositorios de la organización
gfa list-repos --org mycompany --limit 20

# Establecer período de análisis (últimos 6 meses)
gfa config set defaults.months 6

# Analizar tu actividad en repositorio de la organización
gfa feedback --repo mycompany/product-service

# Ver informe (solo muestra tu actividad)
cat reports/report.md
```

</details>

<details>
<summary><b>🎯 Sistema de Premios</b></summary>

Los premios se otorgan automáticamente según la actividad del repositorio:

### Premios Basados en Commits
- 💎 **Leyenda del Código** (1000+ commits)
- 🏆 **Maestro del Código** (500+ commits)
- 🥇 **Herrero del Código** (200+ commits)
- 🥈 **Artesano del Código** (100+ commits)
- 🥉 **Aprendiz del Código** (50+ commits)

### Premios Basados en PR
- 💎 **Leyenda de Releases** (200+ PRs)
- 🏆 **Almirante de Despliegue** (100+ PRs)
- 🥇 **Capitán de Releases** (50+ PRs)
- 🥈 **Navegante de Releases** (25+ PRs)
- 🥉 **Marinero de Despliegue** (10+ PRs)

### Premios Basados en Revisiones
- 💎 **Propagador de Conocimiento** (200+ revisiones)
- 🏆 **Maestro de Mentoría** (100+ revisiones)
- 🥇 **Experto en Revisiones** (50+ revisiones)
- 🥈 **Mentor de Crecimiento** (20+ revisiones)
- 🥉 **Soporte de Código** (10+ revisiones)

### Premios Especiales
- ⚡ **Desarrollador Relámpago** (50+ commits/mes)
- 🤝 **Maestro de Colaboración** (20+ PRs+revisiones/mes)
- 🏗️ **Arquitecto a Gran Escala** (5000+ líneas cambiadas)
- 📅 **Maestro de Consistencia** (6+ meses de actividad continua)
- 🌟 **Multitalento** (Contribuciones equilibradas en todas las áreas)

</details>

<details>
<summary><b>🐛 Solución de Problemas</b></summary>

### Error de Permisos de PAT

```
Error: GitHub API rejected the provided PAT
```

**Solución**: Verifica que el PAT tenga los permisos apropiados
- Repositorios privados: se requiere permiso `repo`
- Repositorios públicos: se requiere permiso `public_repo`
- Verifica en [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)

### Fallo de Conexión al Endpoint LLM

```
Warning: Detailed feedback analysis failed: Connection refused
```

**Solución**:
1. Verifica que el servidor LLM esté en ejecución
2. Verifica que la URL del endpoint sea correcta (`gfa config show`)
3. Reinicializa la configuración si es necesario: `gfa init`

### Repositorio No Encontrado

```
Error: Repository not found
```

**Solución**:
- Verifica el formato del nombre del repositorio: `owner/repo` (ej: `torvalds/linux`)
- Para repositorios privados, verifica los permisos del PAT
- Para GitHub Enterprise, verifica la configuración `--enterprise-host`

### Sin Datos en el Período de Análisis

```
No activity detected during analysis period.
```

**Solución**:
- Intenta aumentar el período de análisis: `gfa init --months 24`
- Verifica que el repositorio esté activo

</details>

<details>
<summary><b>👩‍💻 Guía para Desarrolladores</b></summary>

### Configuración del Entorno de Desarrollo

```bash
# Copiar repositorio
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# Instalar en modo de desarrollo (incluye dependencias de prueba)
uv pip install -e .[test]

# Ejecutar pruebas
pytest

# Ejecutar pruebas específicas
pytest tests/test_analyzer.py -v

# Verificar cobertura
pytest --cov=github_feedback --cov-report=html
```

### Dependencias Principales

**Dependencias principales de ejecución:**
- **typer >= 0.9** - Framework CLI
- **rich >= 13.0** - UI de terminal, barras de progreso
- **pydantic >= 2.5** - Validación y serialización de datos
- **requests >= 2.31** - Cliente HTTP
- **requests-cache >= 1.0** - Caché de respuestas basado en SQLite
- **keyring >= 24.0** - Almacenamiento de credenciales del sistema
- **keyrings.alt >= 5.0** - Llavero de archivo cifrado de respaldo
- **tomli >= 2.0** - Análisis de archivos TOML (Python < 3.11)
- **tomli-w >= 1.0** - Escritura de archivos TOML

**Dependencias de desarrollo/prueba:**
- **pytest >= 7.4** - Framework de pruebas

**Requisitos del sistema:**
- Python 3.11+ (se requieren async/type hints)
- Llavero del sistema o sistema de archivos accesible
- GitHub Personal Access Token (clásico o de grano fino)
- Endpoint LLM compatible con formato de API OpenAI

### Estructura del Código

```
github_feedback/
├── cli.py              # 🖥️  Punto de entrada CLI y comandos (1,791 líneas)
├── llm.py             # 🤖 Cliente de API LLM (1,409 líneas, con lógica de reintento)
├── reporter.py         # 📄 Generación de informes (1,358 líneas, formato brief)
├── retrospective.py    # 📅 Análisis retrospectivo de fin de año (1,021 líneas)
├── analyzer.py         # 📊 Análisis y cálculo de métricas (959 líneas)
├── review_reporter.py  # 📝 Informes de revisión integrados (749 líneas)
├── config.py          # ⚙️  Gestión de configuración (529 líneas, integración de llavero)
├── models.py          # 📦 Modelos de datos Pydantic (525 líneas)
├── pr_collector.py     # 🔍 Recopilación de datos de PR (439 líneas)
├── award_strategies.py # 🏆 Estrategias de cálculo de premios (419 líneas, 100+ premios)
├── api_client.py      # 🌐 Cliente de API REST de GitHub (416 líneas)
├── reviewer.py         # 🎯 Lógica de revisión de PR (416 líneas)
├── collector.py        # 📡 Fachada de recopilación de datos (397 líneas)
├── commit_collector.py # 📝 Recopilación de datos de commits (263 líneas)
├── review_collector.py # 👀 Recopilación de datos de revisión (256 líneas)
├── repository_manager.py # 📂 Gestión de repositorios (250 líneas)
├── filters.py         # 🔍 Detección de idioma y filtrado (234 líneas)
├── exceptions.py      # ⚠️  Jerarquía de excepciones (235 líneas, 24+ tipos de excepciones)
└── utils.py           # 🔧 Funciones utilitarias
```

### Arquitectura y Patrones de Diseño

- **Patrón Fachada**: La clase `Collector` orquesta colectores especializados
- **Patrón Estrategia**: Se usan 100+ estrategias en el cálculo de premios
- **Patrón Repositorio**: `GitHubApiClient` abstrae el acceso a la API
- **Patrón Constructor**: Construcción de informes y métricas
- **Patrón Pool de Hilos**: Recopilación de datos en paralelo (mejora de velocidad 4x)

### Optimizaciones de Rendimiento

- **Caché de solicitudes**: Caché basado en SQLite (`~/.cache/github_feedback/api_cache.sqlite`)
  - Caducidad predeterminada: 1 hora
  - Solo almacena en caché solicitudes GET/HEAD
  - Mejora de velocidad del 60-70% en ejecuciones repetidas
- **Recopilación en paralelo**: Recopilación concurrente de datos usando ThreadPoolExecutor
- **Lógica de reintento**: Retroceso exponencial para solicitudes LLM (máximo 3 intentos)

</details>

## 🔒 Seguridad

- **Almacenamiento de PAT**: Los tokens de GitHub se almacenan de forma segura en el llavero del sistema (no en archivos de texto plano)
  - Soporte de llavero del sistema: gnome-keyring, macOS Keychain, Windows Credential Manager
  - Respaldo de Linux: Llavero de archivo cifrado (`keyrings.alt`)
  - Inicialización de llavero thread-safe (previene condiciones de carrera)
- **Copia de seguridad de configuración**: Crea automáticamente copias de seguridad antes de sobrescribir la configuración
- **Validación de entrada**: Valida todas las entradas del usuario (formato PAT, formato URL, formato de repositorio)
- **Seguridad de caché**: El archivo de caché SQLite tiene permisos de lectura/escritura solo para el usuario
- **Seguridad de API**: Autenticación con token Bearer, comunicación solo HTTPS

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## 🤝 Contribuir

¡Los informes de errores, sugerencias de características y PRs siempre son bienvenidos!

1. Bifurca el repositorio
2. Crea tu rama de características (`git checkout -b feature/amazing-feature`)
3. Confirma tus cambios (`git commit -m 'Add amazing feature'`)
4. Empuja a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 💬 Feedback

Si tienes problemas o sugerencias, ¡regístralos en [Issues](https://github.com/goonbamm/github-feedback-analysis/issues)!
