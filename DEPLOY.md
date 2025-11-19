# Guía de Despliegue - Streamlit Cloud

Esta guía te ayudará a desplegar tu aplicación Streamlit en Streamlit Cloud para que otros usuarios puedan acceder sin necesidad de ejecutar el código localmente.

## ¿Por qué Streamlit Cloud?

- ✅ **Gratuito** para proyectos públicos
- ✅ **Fácil de usar** - solo necesitas un repositorio Git
- ✅ **Despliegue automático** - cada push actualiza la app
- ✅ **Hosting gratuito** - sin necesidad de servidores propios
- ✅ **Diseñado específicamente para Streamlit**

## Requisitos Previos

1. **Cuenta de GitHub** (gratuita)
2. **Cuenta de Streamlit Cloud** (gratuita, se crea con GitHub)
3. **Repositorio Git** con tu código

## Paso 1: Preparar el Repositorio

### 1.1 Inicializar Git (si no lo has hecho)

```bash
cd "/Users/malvayay/Library/CloudStorage/OneDrive-UniversidadAdolfoIbanez/UAI/8° Semestre/Capstone Project/Proyecto_TPF"
git init
```

### 1.2 Asegúrate de que estos archivos estén en el repositorio:

- ✅ `main.py` (tu aplicación principal)
- ✅ `requirements.txt` (dependencias)
- ✅ `.streamlit/config.toml` (configuración de Streamlit)
- ✅ `README.md` (documentación)

### 1.3 Asegúrate de que estos archivos NO estén en el repositorio:

- ❌ `.env` (contiene credenciales sensibles)
- ❌ `venv/` (entorno virtual)
- ❌ `__pycache__/` (archivos de caché)

**Nota:** El archivo `.gitignore` ya está configurado para excluir estos archivos.

### 1.4 Hacer commit de los archivos

```bash
git add .
git commit -m "Preparar proyecto para despliegue en Streamlit Cloud"
```

## Paso 2: Subir a GitHub

### 2.1 Crear un repositorio en GitHub

1. Ve a [GitHub](https://github.com) e inicia sesión
2. Haz clic en el botón **"+"** en la esquina superior derecha
3. Selecciona **"New repository"**
4. Completa:
   - **Repository name:** `tpf-gestion-personal` (o el nombre que prefieras)
   - **Description:** Sistema de Gestión de Personal para Inspecciones Técnicas
   - **Visibility:** 
     - **Public** (recomendado para Streamlit Cloud gratuito)
     - **Private** (requiere plan de pago en Streamlit Cloud)
5. **NO** marques "Initialize with README" (ya tienes uno)
6. Haz clic en **"Create repository"**

### 2.2 Conectar tu repositorio local con GitHub

GitHub te mostrará comandos similares a estos. Ejecútalos en tu terminal:

```bash
git remote add origin https://github.com/TU_USUARIO/tpf-gestion-personal.git
git branch -M main
git push -u origin main
```

**Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.**

## Paso 3: Desplegar en Streamlit Cloud

### 3.1 Crear cuenta en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"Sign up"** o **"Get started"**
3. Selecciona **"Continue with GitHub"**
4. Autoriza a Streamlit Cloud a acceder a tus repositorios

### 3.2 Crear nueva app

1. En el dashboard de Streamlit Cloud, haz clic en **"New app"**
2. Completa el formulario:
   - **Repository:** Selecciona tu repositorio (`tpf-gestion-personal`)
   - **Branch:** `main` (o `master` si usas ese)
   - **Main file path:** `main.py`
   - **App URL:** Se generará automáticamente (puedes personalizarlo)

### 3.3 Configurar Variables de Entorno

**MUY IMPORTANTE:** Necesitas configurar las variables de entorno para que la app funcione.

1. En la página de configuración de tu app, ve a **"Settings"** (⚙️)
2. Desplázate hasta **"Secrets"**
3. Haz clic en **"Open secrets editor"**
4. Agrega las siguientes variables:

```toml
SUPABASE_URL = "https://ftahnaedgxdekeygzbcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0YWhuYWVkZ3hkZWtleWd6YmNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNjEzMDcsImV4cCI6MjA3ODczNzMwN30.4gz6YdmLeInbFSLRBhhIfP-BpSw8eU3mrnp4lPyAchQ"
OPENAI_API_KEY = "tu_openai_api_key_aqui"
```

**⚠️ IMPORTANTE:** Reemplaza `tu_openai_api_key_aqui` con tu API Key real de OpenAI.

5. Haz clic en **"Save"**

### 3.4 Desplegar

1. Haz clic en **"Deploy"** o **"Save"**
2. Streamlit Cloud comenzará a construir y desplegar tu aplicación
3. Esto puede tomar 1-3 minutos la primera vez
4. Una vez completado, verás un enlace a tu aplicación (ej: `https://tpf-gestion-personal.streamlit.app`)

## Paso 4: Compartir tu Aplicación

Una vez desplegada, puedes compartir el enlace con cualquier persona. No necesitan:
- ❌ Instalar Python
- ❌ Instalar dependencias
- ❌ Configurar variables de entorno
- ❌ Ejecutar comandos en terminal

Solo necesitan:
- ✅ Un navegador web
- ✅ El enlace a tu aplicación

## Actualizaciones Futuras

Cada vez que hagas cambios y los subas a GitHub:

```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

Streamlit Cloud **automáticamente** detectará los cambios y volverá a desplegar tu aplicación. Esto toma aproximadamente 1-2 minutos.

## Solución de Problemas

### La app no se despliega

1. Verifica que `main.py` esté en la raíz del repositorio
2. Verifica que `requirements.txt` tenga todas las dependencias
3. Revisa los logs en Streamlit Cloud para ver errores específicos

### Error de variables de entorno

1. Verifica que hayas configurado las variables en "Secrets"
2. Asegúrate de que los nombres sean exactamente:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OPENAI_API_KEY`

### La app funciona localmente pero no en la nube

1. Verifica que todas las dependencias estén en `requirements.txt`
2. Asegúrate de que no estés usando rutas de archivos locales que no existen en la nube
3. Revisa los logs de Streamlit Cloud para ver errores específicos

## Alternativas a Streamlit Cloud

Si prefieres otras opciones:

### Heroku
- ✅ Soporte para Streamlit
- ❌ Requiere configuración más compleja
- ❌ Plan gratuito limitado

### Railway
- ✅ Fácil de usar
- ✅ Plan gratuito generoso
- ⚠️ Requiere configuración de Docker

### Render
- ✅ Plan gratuito disponible
- ⚠️ Requiere configuración adicional

**Recomendación:** Streamlit Cloud es la opción más simple y directa para aplicaciones Streamlit.

## Seguridad

**⚠️ IMPORTANTE:**

1. **NUNCA** subas el archivo `.env` a GitHub
2. **NUNCA** incluyas credenciales en el código
3. Usa siempre variables de entorno para credenciales
4. Si tu repositorio es público, las credenciales en "Secrets" de Streamlit Cloud están seguras (no son visibles públicamente)

## Soporte

- [Documentación de Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- [Foro de Streamlit](https://discuss.streamlit.io/)

