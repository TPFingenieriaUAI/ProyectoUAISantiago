# TPF Ingeniería - Sistema de Gestión de Personal

Sistema SaaS desarrollado con Streamlit, Supabase y OpenAI para procesar y gestionar Curriculums Vitae de personal para inspecciones técnicas de obras.

## Características

- 📄 **Carga y procesamiento automático de CVs** (PDF y DOCX) usando OpenAI
- 🔍 **Búsqueda inteligente de candidatos** según requerimientos específicos
- 👥 **Gestión completa de personal** con edición y filtros
- 📊 **Gestión de proyectos** y asignación de personal
- 👥 **Gestión de clientes** y sus proyectos asociados

## Requisitos Previos

- Python 3.8 o superior
- Cuenta de Supabase
- API Key de OpenAI

## Instalación

1. Clona o descarga este repositorio

2. Crea y activa un entorno virtual (recomendado):

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Configura las variables de entorno:

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# Supabase Configuration
SUPABASE_URL=tu_supabase_url_aqui
SUPABASE_KEY=tu_supabase_key_aqui

# OpenAI Configuration
OPENAI_API_KEY=tu_openai_api_key_aqui
```

**Nota:** Reemplaza los valores con tus credenciales reales:
- Obtén `SUPABASE_URL` y `SUPABASE_KEY` desde tu proyecto en [Supabase Dashboard](https://supabase.com/dashboard)
- Obtén `OPENAI_API_KEY` desde [OpenAI Platform](https://platform.openai.com/api-keys)

## Ejecución

**Asegúrate de tener el entorno virtual activado** (si lo estás usando):

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Para iniciar la aplicación Streamlit:

```bash
streamlit run main.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Desactivar el entorno virtual

Cuando termines de trabajar, puedes desactivar el entorno virtual con:
```bash
deactivate
```

## Estructura de la Base de Datos

### Tabla: `personal`
- `id` (UUID, Primary Key)
- `rut` (VARCHAR, Unique)
- `nombre` (VARCHAR)
- `apellido` (VARCHAR)
- `telefono_personal` (VARCHAR)
- `correo_personal` (VARCHAR)
- `carrera_estudios` (TEXT)
- `experiencia` (TEXT)
- `anos_experiencia` (INTEGER)
- `otros` (TEXT)
- `resumen_ia` (TEXT)
- `cv_url` (TEXT) - URL del CV almacenado en Supabase Storage
- `activo` (BOOLEAN)
- `contratado` (BOOLEAN)
- `proyecto_id` (UUID, Foreign Key a proyectos)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Tabla: `proyectos`
- `id` (UUID, Primary Key)
- `nombre` (VARCHAR)
- `descripcion` (TEXT)
- `cliente_id` (UUID, Foreign Key a clientes)
- `fecha_inicio` (DATE)
- `fecha_fin` (DATE)
- `estado` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Tabla: `clientes`
- `id` (UUID, Primary Key)
- `nombre` (VARCHAR)
- `rut` (VARCHAR, Unique)
- `correo` (VARCHAR)
- `telefono` (VARCHAR)
- `direccion` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Uso

### Cargar un CV

1. Navega a la sección "📄 Cargar CV"
2. Selecciona un archivo PDF o DOCX
3. El sistema procesará automáticamente el CV usando OpenAI
4. Revisa y edita la información extraída si es necesario
5. El sistema subirá automáticamente el CV a Supabase Storage
6. Guarda en la base de datos (el CV quedará asociado al registro)

**Nota:** Los CVs se almacenan en Supabase Storage en un bucket público llamado "cvs" y se puede acceder a ellos desde cualquier lugar donde se visualice la información del personal.

### Buscar Candidatos

1. Navega a la sección "🔍 Buscar Candidatos"
2. Ingresa una descripción detallada de los requerimientos del puesto
3. El sistema utilizará OpenAI para encontrar los mejores candidatos
4. Revisa los resultados ordenados por relevancia

### Gestionar Personal, Proyectos y Clientes

Utiliza las secciones correspondientes para:
- Ver listas de registros
- **Visualizar CVs** directamente en la aplicación (PDFs se muestran embebidos, DOCX se pueden descargar)
- Crear nuevos registros
- Editar registros existentes
- Filtrar y buscar información

### Visualizar CVs

Los CVs almacenados se pueden visualizar en:
- **Página de Gestión de Personal** → Ver Personal: Cada registro muestra el CV si está disponible
- **Página de Gestión de Personal** → Editar Personal: Se muestra el CV antes del formulario de edición
- **Página de Búsqueda de Candidatos**: Los candidatos encontrados muestran su CV si está disponible

Los PDFs se muestran embebidos en la aplicación, mientras que los archivos DOCX deben descargarse para visualizarlos.

## Tecnologías Utilizadas

- **Streamlit**: Framework para la interfaz de usuario
- **Supabase**: Base de datos y backend
- **OpenAI**: Procesamiento de CVs y búsqueda inteligente
- **PyPDF2**: Extracción de texto de archivos PDF
- **python-docx**: Extracción de texto de archivos DOCX

## Notas

- **Recomendado:** Usa un entorno virtual (venv) para mantener las dependencias aisladas
- Las tablas en Supabase ya han sido creadas automáticamente
- El bucket "cvs" en Supabase Storage se crea automáticamente la primera vez que se sube un CV
- Asegúrate de tener una conexión a internet para usar OpenAI y Supabase Storage
- Los CVs se procesan con el modelo `gpt-4o-mini` de OpenAI
- Los CVs se almacenan en Supabase Storage y se puede acceder a ellos mediante URLs públicas

## Despliegue en la Nube

Para que otros usuarios puedan acceder a tu aplicación sin necesidad de ejecutarla localmente, puedes desplegarla en **Streamlit Cloud** (gratuito y recomendado).

📖 **Consulta la guía completa de despliegue en [DEPLOY.md](DEPLOY.md)**

### Resumen rápido:

1. Sube tu código a GitHub
2. Crea una cuenta en [Streamlit Cloud](https://share.streamlit.io)
3. Conecta tu repositorio
4. Configura las variables de entorno en "Secrets"
5. ¡Listo! Tu app estará disponible públicamente

**Alternativas:** También puedes usar Heroku, Railway, Render u otras plataformas, pero Streamlit Cloud es la más simple para aplicaciones Streamlit.

## Archivos a incluir al compartir el proyecto

Si vas a compartir este proyecto, asegúrate de incluir:
- `main.py`
- `requirements.txt`
- `README.md`
- `.streamlit/config.toml` (configuración de Streamlit)
- `DEPLOY.md` (guía de despliegue)

**NO incluyas:**
- `.env` (contiene credenciales sensibles - **NUNCA lo subas a repositorios públicos**)
- `venv/` (el entorno virtual se crea localmente)
- `__pycache__/` (archivos de caché de Python)

