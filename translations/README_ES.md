# 🚀 Análisis de Feedback de GitHub

Una herramienta CLI que analiza la actividad de repositorios de GitHub y genera automáticamente informes perspicaces. Compatible con GitHub.com y GitHub Enterprise, con capacidades de revisión automatizada basadas en LLM.

Español | [한국어](../README.md) | [English](README_EN.md) | [简体中文](README_ZH.md) | [日本語](README_JA.md)

## ✨ Características Principales

- 📊 **Análisis de Repositorios**: Agrega y analiza commits, issues y actividad de revisión por período
- 🤖 **Feedback Basado en LLM**: Análisis detallado de mensajes de commit, títulos de PR, tono de revisión y calidad de issues
- 🎯 **Revisión Automática de PR**: Revisa automáticamente los PRs de usuarios autenticados y genera informes retrospectivos integrados
- 🏆 **Visualización de Logros**: Genera automáticamente premios y destacados basados en contribuciones
- 💡 **Descubrimiento de Repositorios**: Lista repositorios accesibles y sugiere los activos
- 🎨 **Modo Interactivo**: Interfaz amigable para selección directa de repositorios

## 📋 Requisitos Previos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/) o su gestor de paquetes preferido
- GitHub Personal Access Token
  - Repositorios privados: permiso `repo`
  - Repositorios públicos: permiso `public_repo`
- Endpoint de API LLM (formato compatible con OpenAI)

## 🔑 Generar GitHub Personal Access Token

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
   - Ingresar el token copiado al ejecutar `gfainit`

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
   gfainit --enterprise-host https://github.your-company.com
   ```

4. **Contactar al Administrador**
   - La generación de PAT puede estar restringida en algunos entornos Enterprise
   - Contacte a su administrador de GitHub si encuentra problemas

### Referencias

- [Documentación de GitHub: Gestión de Personal Access Tokens](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Documentación de GitHub: Fine-grained PAT](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [Documentación de GitHub Enterprise Server](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## 🔧 Instalación

```bash
# Clonar el repositorio
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
gfainit
```

Cuando se le solicite, ingrese la siguiente información:
- GitHub Personal Access Token (almacenado de forma segura en el llavero del sistema)
- Endpoint LLM (ej: `http://localhost:8000/v1/chat/completions`)
- Modelo LLM (ej: `gpt-4`)
- Host de GitHub Enterprise (opcional, solo si no usa github.com)

### 2️⃣ Analizar Repositorio

```bash
gfa feedback --repo goonbamm/github-feedback-analysis
```

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

### 🎯 `gfainit` - Configuración Inicial

Almacena información de acceso a GitHub y configuración de LLM.

#### Uso Básico (Interactivo)

```bash
gfainit
```

#### Ejemplo: GitHub.com + LLM Local

```bash
gfainit \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### Ejemplo: GitHub Enterprise

```bash
gfainit \
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

### 📊 `gfa feedback` - Análisis de Repositorio

Analiza el repositorio y genera informes de feedback detallados.

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
# Analizar repositorio público
gfa feedback --repo torvalds/linux

# Analizar repositorio personal
gfa feedback --repo myusername/my-private-repo

# Analizar repositorio de organización
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
├── metrics.json              # 📈 Datos de análisis sin procesar
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

#### Contenido del Análisis

- ✅ **Agregación de Actividad**: Cuenta commits, PRs, revisiones e issues
- 🎯 **Análisis de Calidad**: Mensajes de commit, títulos de PR, tono de revisión, calidad de descripción de issues
- 🏆 **Premios**: Premios automáticos basados en contribuciones
- 📈 **Tendencias**: Tendencias de actividad mensual y análisis de velocidad

### 🎯 `gfafeedback` - Revisión Automática de PR

Revisa automáticamente los PRs del usuario autenticado (propietario del PAT) y genera un informe retrospectivo integrado.

#### Uso Básico

```bash
gfafeedback --repo owner/repo-name
```

#### Ejemplos

```bash
# Revisar todos los PRs creados por ti
gfafeedback --repo myusername/my-project
```

#### Opciones

| Opción | Descripción | Requerido | Predeterminado |
|--------|-------------|-----------|----------------|
| `--repo` | Repositorio (owner/name) | ✅ | - |

#### Proceso de Ejecución

1. **Búsqueda de PR** 🔍
   - Recupera la lista de PRs creados por el usuario autenticado con PAT

2. **Generar Revisiones Individuales** 📝
   - Recopila cambios de código y comentarios de revisión para cada PR
   - Genera revisiones detalladas usando LLM
   - Guarda en el directorio `reviews/owner_repo/pr-{número}/`

3. **Informe Retrospectivo Integrado** 📊
   - Genera insights combinando todos los PRs
   - Guarda en `reviews/owner_repo/integrated_report.md`

#### Archivos Generados

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # Datos sin procesar del PR
    │   ├── review_summary.json     # Resultados del análisis LLM
    │   └── review.md               # Revisión en Markdown
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # Informe retrospectivo integrado
```

### ⚙️ `gfaconfig` - Gestión de Configuración

Ver o modificar la configuración.

#### `gfaconfig show` - Ver Configuración

Ver la configuración actualmente almacenada.

```bash
gfaconfig show
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

> **Nota:** El comando `gfashow-config` está obsoleto y ha sido reemplazado por `gfaconfig show`.

#### `gfaconfig set` - Establecer Valores de Configuración

Modifica valores de configuración individuales.

```bash
gfaconfig set <key> <value>
```

**Ejemplos:**

```bash
# Cambiar modelo LLM
gfaconfig set llm.model gpt-4

# Cambiar endpoint LLM
gfaconfig set llm.endpoint http://localhost:8000/v1/chat/completions

# Cambiar período de análisis predeterminado
gfaconfig set defaults.months 6
```

#### `gfaconfig get` - Obtener Valores de Configuración

Recupera valores de configuración específicos.

```bash
gfaconfig get <key>
```

**Ejemplos:**

```bash
# Verificar modelo LLM
gfaconfig get llm.model

# Verificar período de análisis predeterminado
gfaconfig get defaults.months
```

### 🔍 `gfalist-repos` - Listar Repositorios

Lista los repositorios accesibles.

```bash
gfalist-repos
```

#### Ejemplos

```bash
# Listar repositorios (predeterminado: 20 actualizados recientemente)
gfalist-repos

# Cambiar criterio de ordenamiento
gfalist-repos --sort stars --limit 10

# Filtrar por organización específica
gfalist-repos --org myorganization

# Ordenar por fecha de creación
gfalist-repos --sort created --limit 50
```

#### Opciones

| Opción | Descripción | Predeterminado |
|--------|-------------|----------------|
| `--sort`, `-s` | Criterio de ordenamiento (updated, created, pushed, full_name) | updated |
| `--limit`, `-l` | Número máximo a mostrar | 20 |
| `--org`, `-o` | Filtrar por nombre de organización | - |

### 💡 `gfasuggest-repos` - Sugerencias de Repositorios

Sugiere repositorios activos adecuados para análisis.

```bash
gfasuggest-repos
```

Selecciona automáticamente repositorios con actividad reciente. Considera de manera integral estrellas, forks, issues y actualizaciones recientes.

#### Ejemplos

```bash
# Sugerencias predeterminadas (dentro de los últimos 90 días, 10 repositorios)
gfasuggest-repos

# Sugerir 5 repositorios activos en los últimos 30 días
gfasuggest-repos --limit 5 --days 30

# Ordenar por estrellas
gfasuggest-repos --sort stars

# Ordenar por puntuación de actividad (evaluación integral)
gfasuggest-repos --sort activity
```

#### Opciones

| Opción | Descripción | Predeterminado |
|--------|-------------|----------------|
| `--limit`, `-l` | Número máximo de sugerencias | 10 |
| `--days`, `-d` | Período de actividad reciente (días) | 90 |
| `--sort`, `-s` | Criterio de ordenamiento (updated, stars, activity) | activity |

## 📁 Archivo de Configuración

La configuración se almacena en `~/.config/github_feedback/config.toml` y se crea automáticamente al ejecutar `gfainit`.

### Ejemplo de Archivo de Configuración

```toml
[version]
version = "1.0.0"

[auth]
# PAT se almacena de forma segura en el llavero del sistema (no en este archivo)

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

Si es necesario, puede editar el archivo de configuración directamente o usar los comandos `gfaconfig`:

```bash
# Método 1: Usar comandos config (recomendado)
gfaconfig set llm.model gpt-4
gfaconfig show

# Método 2: Edición directa
nano ~/.config/github_feedback/config.toml
```

## 📊 Estructura de Archivos Generados

### Salida de `gfa feedback`

```
reports/
├── metrics.json              # 📈 Datos de análisis sin procesar
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

### Salida de `gfafeedback`

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # 📦 Datos sin procesar del PR (código, revisiones, etc.)
    │   ├── review_summary.json     # 🤖 Resultados del análisis LLM (datos estructurados)
    │   └── review.md               # 📝 Informe de revisión en Markdown
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 🎯 Informe retrospectivo integrado (todos los PRs combinados)
```

## 💡 Ejemplos de Uso

### Ejemplo 1: Inicio Rápido - Modo Interactivo

```bash
# 1. Configuración (solo la primera vez)
gfainit

# 2. Obtener sugerencias de repositorios
gfasuggest-repos

# 3. Analizar con modo interactivo
gfa feedback --interactive

# 4. Ver informe
cat reports/report.md
```

### Ejemplo 2: Análisis de Proyecto de Código Abierto

```bash
# 1. Configuración (solo la primera vez)
gfainit

# 2. Analizar proyecto popular de código abierto
gfa feedback --repo facebook/react

# 3. Ver informe
cat reports/report.md
```

### Ejemplo 3: Retrospectiva de Proyecto Personal

```bash
# Verificar lista de mis repositorios
gfalist-repos --sort updated --limit 10

# Analizar mi proyecto
gfa feedback --repo myname/my-awesome-project

# Revisar automáticamente mis PRs
gfafeedback --repo myname/my-awesome-project

# Ver informe retrospectivo integrado
cat reviews/myname_my-awesome-project/integrated_report.md
```

### Ejemplo 4: Revisión de Rendimiento de Proyecto de Equipo

```bash
# Verificar lista de repositorios de la organización
gfalist-repos --org mycompany --limit 20

# Establecer período de análisis (últimos 6 meses)
gfaconfig set defaults.months 6

# Analizar repositorio de la organización
gfa feedback --repo mycompany/product-service

# Revisar PRs de miembros del equipo (cada uno ejecuta con su propio PAT)
gfafeedback --repo mycompany/product-service
```

## 🎯 Sistema de Premios

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

## 🐛 Solución de Problemas

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
2. Verifica que la URL del endpoint sea correcta (`gfaconfig show`)
3. Reinicializa la configuración si es necesario: `gfainit`

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
- Intenta aumentar el período de análisis: `gfainit --months 24`
- Verifica que el repositorio esté activo

## 👩‍💻 Guía para Desarrolladores

### Configuración del Entorno de Desarrollo

```bash
# Clonar repositorio
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

### Estructura del Código

```
github_feedback/
├── cli.py              # 🖥️  Punto de entrada CLI y comandos
├── collector.py        # 📡 Recopilación de datos de API de GitHub
├── analyzer.py         # 📊 Análisis y cálculo de métricas
├── reporter.py         # 📄 Generación de informes (brief)
├── reviewer.py         # 🎯 Lógica de revisión de PR
├── review_reporter.py  # 📝 Informes de revisión integrados
├── llm.py             # 🤖 Cliente de API LLM
├── config.py          # ⚙️  Gestión de configuración
├── models.py          # 📦 Modelos de datos
└── utils.py           # 🔧 Funciones utilitarias
```

## 🔒 Seguridad

- **Almacenamiento de PAT**: Los tokens de GitHub se almacenan de forma segura en el llavero del sistema (no en archivos de texto plano)
- **Respaldo de Configuración**: Crea automáticamente respaldos antes de sobrescribir la configuración
- **Validación de Entrada**: Valida todas las entradas del usuario (formato PAT, formato URL, formato de repositorio)

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
