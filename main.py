import streamlit as st
import os
from supabase import create_client, Client
from openai import OpenAI
import PyPDF2
import docx
from io import BytesIO
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de página
st.set_page_config(
	page_title="TPF Ingeniería - Gestión de Personal",
	page_icon=None,
	layout="wide",
	initial_sidebar_state="expanded"
)

# CSS personalizado para el tema azul oscuro y celeste
st.markdown("""
	<style>
		/* Fondo principal azul oscuro */
		.stApp {
			background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
		}
		
		/* Sidebar azul oscuro */
		[data-testid="stSidebar"] {
			background: linear-gradient(180deg, #0d1b2a 20%, #1b263b 100%);
		}
		
		/* Títulos y texto principal */
		h1, h2, h3 {
			color: #87ceeb !important; /* Celeste */
		}
		
		/* Texto general */
		.main .block-container {
			color: #e0e0e0;
		}
		
		/* Botones primarios - celeste */
		.stButton > button {
			background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
			color: #0a1929;
			border: none;
			border-radius: 8px;
			font-weight: 600;
			transition: all 0.3s ease;
		}
		
		.stButton > button:hover {
			background: linear-gradient(135deg, #29b6f6 0%, #0288d1 100%);
			transform: translateY(-2px);
			box-shadow: 0 4px 12px rgba(79, 195, 247, 0.4);
		}
		
		/* Cards y contenedores */
		[data-testid="stExpander"] {
			background-color: rgba(26, 35, 50, 0.8);
			border: 1px solid rgba(135, 206, 235, 0.2);
			border-radius: 10px;
		}
		
		/* Inputs y text areas */
		.stTextInput > div > div > input,
		.stTextArea > div > div > textarea {
			background-color: rgba(26, 35, 50, 0.6);
			color: #e0e0e0;
			border: 1px solid rgba(135, 206, 235, 0.3);
			border-radius: 6px;
		}
		
		.stTextInput > div > div > input:focus,
		.stTextArea > div > div > textarea:focus {
			border-color: #4fc3f7;
			box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.2);
		}
		
		/* Selectbox y radio */
		.stSelectbox > div > div > select,
		.stRadio > div {
			background-color: rgba(26, 35, 50, 0.6);
			color: #e0e0e0;
		}
		
		/* Tabs */
		[data-baseweb="tab-list"] {
			background-color: rgba(26, 35, 50, 0.6);
			border-radius: 8px;
		}
		
		[data-baseweb="tab"] {
			color: #87ceeb;
		}
		
		[data-baseweb="tab"][aria-selected="true"] {
			background-color: rgba(79, 195, 247, 0.2);
			color: #4fc3f7;
		}
		
		/* Métricas */
		[data-testid="stMetricValue"] {
			color: #4fc3f7;
		}
		
		/* Success messages */
		.stSuccess {
			background-color: rgba(79, 195, 247, 0.1);
			border-left: 4px solid #4fc3f7;
		}
		
		/* Info boxes */
		.stInfo {
			background-color: rgba(26, 35, 50, 0.8);
			border-left: 4px solid #87ceeb;
		}
		
		/* Logo container */
		.logo-container {
			text-align: center;
			padding: 20px 0;
			margin-bottom: 20px;
		}
		
		.logo-container img {
			max-width: 200px;
			height: auto;
		}
		
		/* Scrollbar personalizado */
		::-webkit-scrollbar {
			width: 8px;
		}
		
		::-webkit-scrollbar-track {
			background: #0a1929;
		}
		
		::-webkit-scrollbar-thumb {
			background: #4fc3f7;
			border-radius: 4px;
		}
		
		::-webkit-scrollbar-thumb:hover {
			background: #29b6f6;
		}
	</style>
	""", unsafe_allow_html=True)

# Inicializar variables de sesión
if 'supabase' not in st.session_state:
	st.session_state.supabase = None
if 'openai_client' not in st.session_state:
	st.session_state.openai_client = None

# Función para inicializar clientes
def init_clients():
	"""Inicializa los clientes de Supabase y OpenAI"""
	if st.session_state.supabase is None:
		supabase_url = os.getenv("SUPABASE_URL")
		supabase_key = os.getenv("SUPABASE_KEY")
		
		if not supabase_url or not supabase_key:
			st.error("⚠️ Por favor configura SUPABASE_URL y SUPABASE_KEY en las variables de entorno")
			return False
		
		st.session_state.supabase = create_client(supabase_url, supabase_key)
	
	if st.session_state.openai_client is None:
		openai_key = os.getenv("OPENAI_API_KEY")
		
		if not openai_key:
			st.error("⚠️ Por favor configura OPENAI_API_KEY en las variables de entorno")
			return False
		
		st.session_state.openai_client = OpenAI(api_key=openai_key)
	
	return True

# Función para normalizar RUT (solo primeros 8 dígitos, sin puntos, guiones ni dígito verificador)
def normalize_rut(rut: Optional[str]) -> Optional[str]:
	"""Normaliza un RUT extrayendo solo los primeros 8 dígitos numéricos"""
	if not rut:
		return None
	
	# Convertir a string y limpiar
	rut_str = str(rut).strip()
	
	# Remover puntos, guiones, espacios y cualquier carácter no numérico
	rut_clean = ''.join(c for c in rut_str if c.isdigit())
	
	# Si no hay dígitos, retornar None
	if not rut_clean:
		return None
	
	# Tomar solo los primeros 8 dígitos
	rut_normalized = rut_clean[:8]
	
	# Si tiene menos de 8 dígitos, rellenar con ceros a la izquierda (opcional)
	# O simplemente retornar lo que hay
	if len(rut_normalized) < 8:
		# Opción 1: Retornar tal cual (puede tener menos de 8 dígitos)
		# Opción 2: Rellenar con ceros (descomentar si prefieres)
		# rut_normalized = rut_normalized.zfill(8)
		pass
	
	return rut_normalized

# Función para extraer texto de PDF
def extract_text_from_pdf(file) -> str:
	"""Extrae texto de un archivo PDF"""
	try:
		pdf_reader = PyPDF2.PdfReader(file)
		text = ""
		for page in pdf_reader.pages:
			text += page.extract_text()
		return text
	except Exception as e:
		st.error(f"Error al leer PDF: {str(e)}")
		return ""

# Función para extraer texto de DOCX
def extract_text_from_docx(file) -> str:
	"""Extrae texto de un archivo DOCX"""
	try:
		doc = docx.Document(file)
		text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
		return text
	except Exception as e:
		st.error(f"Error al leer DOCX: {str(e)}")
		return ""

# Función para procesar CV con OpenAI
def process_cv_with_ai(cv_text: str) -> Dict[str, Any]:
	"""Procesa el CV con OpenAI y extrae la información estructurada"""
	client = st.session_state.openai_client
	
	prompt = f"""Analiza el siguiente Curriculum Vitae y extrae la información en formato JSON. 
	Responde SOLO con un JSON válido, sin texto adicional antes o después.

	Campos requeridos:
	- rut: RUT o documento de identidad (string)
	- nombre: Nombre completo o solo nombre (string)
	- apellido: Apellido(s) (string)
	- telefono_personal: Teléfono de contacto (string o null)
	- correo_personal: Correo electrónico (string o null)
	- carrera_estudios: Carrera o estudios realizados (string o null)
	- experiencia: Descripción de la experiencia laboral (string o null)
	- anos_experiencia: Años de experiencia (número entero o null)
	- certificaciones: Certificaciones, licencias, cursos, capacitaciones o acreditaciones profesionales (string o null). Lista todas las certificaciones encontradas separadas por comas o punto y coma.
	- otros: Cualquier otra información relevante (string o null)
	- resumen_ia: Un resumen profesional del candidato hecho por IA (string)

	Si algún campo no está disponible en el CV, usa null para ese campo.
	El resumen_ia debe ser un resumen profesional de 2-3 párrafos sobre el candidato.

	CV:
	{cv_text[:4000]}  # Limitar a 4000 caracteres para evitar tokens excesivos
	"""
	
	try:
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{"role": "system", "content": "Eres un asistente experto en extraer información de CVs. Responde SOLO con JSON válido."},
				{"role": "user", "content": prompt}
			],
			temperature=0.3,
			response_format={"type": "json_object"}
		)
		
		result = json.loads(response.choices[0].message.content)
		return result
	except Exception as e:
		st.error(f"Error al procesar CV con IA: {str(e)}")
		return {}

# Función para asegurar que el bucket existe
def ensure_bucket_exists(supabase, bucket_name: str = "cvs"):
	"""Asegura que el bucket existe, si no, intenta crearlo"""
	try:
		# Intentar listar buckets para verificar si existe
		buckets = supabase.storage.list_buckets()
		bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
		
		if not bucket_exists:
			# Intentar crear el bucket como público
			try:
				supabase.storage.create_bucket(
					bucket_name,
					{
						"public": True,
						"allowed_mime_types": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
						"file_size_limit": 10485760  # 10MB
					}
				)
				return True
			except Exception as create_error:
				# Si falla la creación con opciones avanzadas, intentar con opciones básicas
				try:
					supabase.storage.create_bucket(bucket_name, {"public": True})
					return True
				except Exception as e2:
					# Si el error es que ya existe, está bien
					error_str = str(e2).lower()
					if "already exists" in error_str or "duplicate" in error_str or "bucket already exists" in error_str:
						return True
					# Si es un error de permisos, lanzar un error más descriptivo
					if "permission" in error_str or "403" in error_str or "unauthorized" in error_str:
						raise Exception(
							f"No tienes permisos para crear el bucket '{bucket_name}'. "
							f"Por favor, créalo manualmente en el dashboard de Supabase:\n"
							f"1. Ve a tu proyecto en Supabase\n"
							f"2. Navega a Storage\n"
							f"3. Crea un nuevo bucket llamado '{bucket_name}'\n"
							f"4. Configúralo como público (public)"
						)
					# Otro error, lanzarlo
					raise e2
		return True
	except Exception as e:
		# Re-lanzar el error con más contexto
		raise e

# Función para subir CV a Supabase Storage
def upload_cv_to_storage(file, rut: str, file_extension: str) -> Optional[str]:
	"""Sube un archivo CV a Supabase Storage y retorna la URL pública"""
	try:
		supabase = st.session_state.supabase
		
		# Asegurar que el bucket existe
		ensure_bucket_exists(supabase, "cvs")
		
		# Leer el contenido del archivo como bytes
		file.seek(0)  # Asegurarse de que estamos al inicio del archivo
		file_content = file.read()
		
		# Asegurar que el contenido es bytes
		if isinstance(file_content, str):
			file_content = file_content.encode('utf-8')
		elif not isinstance(file_content, bytes):
			# Si no es bytes ni string, intentar convertirlo
			file_content = bytes(file_content)
		
		# Crear nombre único para el archivo usando RUT normalizado y timestamp
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		
		# Normalizar RUT (solo primeros 8 dígitos)
		clean_rut = normalize_rut(rut)
		
		# Si el RUT normalizado está vacío, usar un valor por defecto
		if not clean_rut:
			clean_rut = "cv"
		
		# Crear el nombre del archivo - formato simple y seguro
		file_name = f"{clean_rut}_{timestamp}.{file_extension}"
		
		# Validación final: asegurar que es un string ASCII válido y no está vacío
		file_name = str(file_name).strip()
		
		# Validar que no esté vacío
		if not file_name or len(file_name) == 0:
			file_name = f"cv_{timestamp}.{file_extension}"
		
		# Validar que sea ASCII
		try:
			file_name.encode('ascii')
		except UnicodeEncodeError:
			# Si tiene caracteres no ASCII, usar solo timestamp
			file_name = f"cv_{timestamp}.{file_extension}"
		
		# Validación adicional: asegurar que el nombre no tenga caracteres problemáticos
		# Reemplazar cualquier carácter que no sea alfanumérico, punto, guión bajo o guión
		import re
		file_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file_name)
		
		# Asegurar que el nombre no empiece con punto o guión
		file_name = file_name.lstrip('.-_')
		
		# Si después de todo esto está vacío, usar un nombre por defecto
		if not file_name or len(file_name) == 0:
			file_name = f"cv_{timestamp}.{file_extension}"
		
		# Determinar content-type
		content_type = "application/pdf" if file_extension == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
		if hasattr(file, 'type') and file.type:
			content_type = file.type
		
		# Convertir el contenido a BytesIO para asegurar compatibilidad
		from io import BytesIO
		file_bytes = BytesIO(file_content)
		
		# Resetear el puntero del archivo original para poder leerlo de nuevo si es necesario
		file.seek(0)
		
		# Asegurar que file_name es exactamente un string simple (no bytes, no None, no objeto)
		file_name = str(file_name).strip()
		
		# Validación final: asegurar que es un string válido y no está vacío
		if not file_name or not isinstance(file_name, str):
			file_name = f"cv_{timestamp}.{file_extension}"
		
		# Limpiar el nombre del archivo de caracteres problemáticos
		file_name_str = re.sub(r'[^a-zA-Z0-9._-]', '_', file_name)
		file_name_str = file_name_str.lstrip('.-_')
		
		# Si después de limpiar está vacío, usar un nombre por defecto
		if not file_name_str or len(file_name_str) == 0:
			file_name_str = f"cv_{timestamp}.{file_extension}"
		
		# Método Único y Robusto: Usar argumentos de palabra clave (kwargs)
		# Esto elimina cualquier ambigüedad sobre el orden de los parámetros
		try:
			response = supabase.storage.from_("cvs").upload(
				path=file_name_str,  # 1. Nombre de archivo (string) - argumento de palabra clave
				file=file_content,   # 2. Contenido binario (bytes) - argumento de palabra clave
				file_options={"content-type": content_type, "upsert": True}
			)
			
			# Verificar que la subida fue exitosa
			if response and 'error' not in str(response):
				# Obtener URL pública
				url_response = supabase.storage.from_("cvs").get_public_url(file_name_str)
				return url_response
			else:
				# Si hay una respuesta pero con error
				error_msg = response.get('error', 'Error desconocido en la respuesta de Supabase') if isinstance(response, dict) else str(response)
				raise Exception(f"Error en la respuesta de Supabase: {error_msg}")
		except Exception as e:
			# Re-lanzar el error para que sea manejado por el bloque try-except externo
			raise e
			
	except Exception as e:
		error_msg = str(e)
		st.error(f"Error al subir CV a Storage: {error_msg}")
		
		# Mostrar detalles del error para debugging
		if hasattr(e, 'message'):
			st.error(f"Detalles del error: {e.message}")
		
		# Si el error es que el bucket no existe, mostrar instrucciones
		if "bucket not found" in error_msg.lower() or "404" in error_msg.lower():
			st.warning("""
			**El bucket 'cvs' no existe en Supabase Storage.**
			
			Por favor, créalo manualmente:
			1. Ve a tu proyecto en Supabase: https://supabase.com/dashboard
			2. Selecciona tu proyecto
			3. Ve a la sección **Storage** en el menú lateral
			4. Haz clic en **"New bucket"** o **"Crear bucket"**
			5. Nombre del bucket: **cvs**
			6. Marca la opción **"Public bucket"** (bucket público)
			7. Haz clic en **"Create bucket"**
			
			Una vez creado, intenta subir el CV nuevamente.
			""")
		elif "must be string" in error_msg.lower():
			st.warning("""
			**Error en el formato del nombre del archivo.**
			
			Esto puede deberse a caracteres especiales en el RUT o nombre del archivo.
			Por favor, verifica que el RUT solo contenga números y letras.
			""")
		
		return None

# Función para guardar personal en Supabase
def save_personal_to_db(data: Dict[str, Any], cv_url: Optional[str] = None) -> bool:
	"""Guarda la información del personal en Supabase"""
	try:
		supabase = st.session_state.supabase
		
		# Normalizar RUT antes de guardar (solo primeros 8 dígitos)
		rut_normalized = normalize_rut(data.get("rut"))
		
		# Preparar datos para insertar
		personal_data = {
			"rut": rut_normalized,  # RUT normalizado (solo primeros 8 dígitos)
			"nombre": data.get("nombre", ""),
			"apellido": data.get("apellido", ""),
			"telefono_personal": data.get("telefono_personal"),
			"correo_personal": data.get("correo_personal"),
			"carrera_estudios": data.get("carrera_estudios"),
			"experiencia": data.get("experiencia"),
			"anos_experiencia": data.get("anos_experiencia"),
			"certificaciones": data.get("certificaciones"),
			"otros": data.get("otros"),
			"resumen_ia": data.get("resumen_ia"),
			"activo": True,
			"contratado": False
		}
		
		# Agregar URL del CV si está disponible
		if cv_url:
			personal_data["cv_url"] = cv_url
		
		# Verificar si ya existe un registro con el mismo RUT normalizado
		if personal_data["rut"]:
			existing = supabase.table("personal").select("id").eq("rut", personal_data["rut"]).execute()
			if existing.data:
				# Actualizar registro existente
				supabase.table("personal").update(personal_data).eq("rut", personal_data["rut"]).execute()
				return True
		
		# Insertar nuevo registro
		supabase.table("personal").insert(personal_data).execute()
		return True
	except Exception as e:
		st.error(f"Error al guardar en base de datos: {str(e)}")
		return False

# Función para buscar candidatos con OpenAI
def search_candidates_with_ai(description: str) -> list:
	"""Busca los mejores candidatos según la descripción usando OpenAI"""
	supabase = st.session_state.supabase
	client = st.session_state.openai_client
	
	try:
		# Obtener todos los candidatos activos Y NO contratados (disponibles para asignar)
		response = supabase.table("personal").select("*").eq("activo", True).eq("contratado", False).execute()
		candidates = response.data
		
		if not candidates:
			return []
		
		# Crear contexto con información de candidatos
		candidates_context = []
		for candidate in candidates:
			puntuacion = candidate.get('puntuacion_calidad')
			puntuacion_texto = f"{puntuacion}/5 ⭐" if puntuacion else "Sin puntuación"
			candidate_info = f"""
			ID: {candidate['id']}
			Nombre: {candidate.get('nombre', '')} {candidate.get('apellido', '')}
			RUT: {candidate.get('rut', '')}
			Carrera/Estudios: {candidate.get('carrera_estudios', 'N/A')}
			Años de experiencia: {candidate.get('anos_experiencia', 'N/A')}
			Experiencia: {candidate.get('experiencia', 'N/A')}
			Certificaciones: {candidate.get('certificaciones', 'N/A')}
			Resumen IA: {candidate.get('resumen_ia', 'N/A')}
			Puntuación de Calidad: {puntuacion_texto}
			"""
			candidates_context.append(candidate_info)
		
		context = "\n---\n".join(candidates_context)
		
		# Para bases de datos grandes, necesitamos optimizar el contexto
		# Si hay muchos candidatos, limitar la información por candidato pero incluir todos
		# Calcular el límite dinámico basado en el número de candidatos
		# OpenAI tiene límites de tokens, pero podemos usar hasta ~100k tokens (aproximadamente 400k caracteres)
		# Para seguridad, usaremos un límite más conservador pero generoso
		max_context_length = 100000  # ~100k caracteres debería ser suficiente para muchos candidatos
		
		if len(context) > max_context_length:
			# Si el contexto es muy largo, optimizar la información por candidato
			# Reducir campos largos pero mantener la información esencial
			optimized_context = []
			for candidate_info in candidates_context:
				# Limitar la longitud de cada candidato a ~500 caracteres
				if len(candidate_info) > 500:
					# Mantener las primeras líneas importantes y truncar campos largos
					lines = candidate_info.split('\n')
					essential_lines = []
					for line in lines:
						if any(keyword in line for keyword in ['ID:', 'Nombre:', 'RUT:', 'Carrera/Estudios:', 'Años de experiencia:', 'Certificaciones:', 'Puntuación de Calidad:']):
							essential_lines.append(line[:200])  # Limitar cada línea a 200 caracteres
					candidate_info = '\n'.join(essential_lines[:15])  # Máximo 15 líneas por candidato
				optimized_context.append(candidate_info)
			context = "\n---\n".join(optimized_context)
		
		# Usar todo el contexto disponible (sin truncar arbitrariamente)
		context_truncated = context
		
		# Contar cuántos candidatos hay
		total_candidates = len(candidates)
		
		prompt = f"""Basándote en la siguiente descripción de requerimientos y la lista de candidatos disponibles, 
		selecciona y ordena TODOS los candidatos disponibles por relevancia.

		IMPORTANTE: 
		- Hay {total_candidates} candidatos disponibles en total. DEBES incluir TODOS en tu respuesta.
		- La puntuación de calidad (1-5 estrellas) es el SEGUNDO criterio más importante después de la relevancia técnica. 
		- Prioriza candidatos con puntuaciones más altas cuando tengan relevancia técnica similar.

		Requerimientos:
		{description}

		Candidatos disponibles:
		{context_truncated}

		Responde SOLO con un JSON que contenga un array "candidatos" con objetos que tengan:
		- id: El ID del candidato
		- relevancia: Un score del 1-10 (considera tanto la relevancia técnica como la puntuación de calidad)
		- razon: Breve explicación de por qué es adecuado (menciona la puntuación de calidad si está disponible)

		CRÍTICO: Debes incluir TODOS los {total_candidates} candidatos en tu respuesta, ordenados por relevancia descendente.
		No omitas ningún candidato, incluso si su relevancia es baja.
		"""
		
		ai_response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{"role": "system", "content": "Eres un asistente experto en selección de personal. Responde SOLO con JSON válido."},
				{"role": "user", "content": prompt}
			],
			temperature=0.3,
			response_format={"type": "json_object"}
		)
		
		result = json.loads(ai_response.choices[0].message.content)
		recommended_ids = [c["id"] for c in result.get("candidatos", [])]
		
		# Obtener información completa de los candidatos recomendados
		recommended_candidates = []
		for candidate in candidates:
			if candidate["id"] in recommended_ids:
				recommended_candidates.append(candidate)
		
		# Verificar si faltan candidatos (ChatGPT podría no haber incluido todos)
		all_candidate_ids = {c["id"] for c in candidates}
		missing_ids = all_candidate_ids - set(recommended_ids)
		
		# Agregar los candidatos faltantes al final con relevancia 0
		if missing_ids:
			for candidate in candidates:
				if candidate["id"] in missing_ids:
					recommended_candidates.append(candidate)
		
		# Ordenar según el orden de recomendación (los recomendados primero, luego los faltantes)
		if recommended_ids:
			recommended_candidates.sort(key=lambda x: recommended_ids.index(x["id"]) if x["id"] in recommended_ids else len(recommended_ids))
		
		return recommended_candidates
	except Exception as e:
		st.error(f"Error al buscar candidatos: {str(e)}")
		return []

# Página de Inicio
def page_inicio():
	st.title("TPF Ingeniería")
	st.markdown("### Bienvenido al Sistema de Gestión de Personal para Inspecciones Técnicas")
	st.markdown("Utiliza el menú lateral para navegar entre las diferentes secciones")
	
	st.markdown("---")
	
	# Intentar cargar métricas si los clientes están inicializados
	if init_clients():
		supabase = st.session_state.supabase
		
		try:
			# Obtener métricas
			personal_activo = supabase.table("personal").select("id").eq("activo", True).execute()
			proyectos_activos = supabase.table("proyectos").select("id").eq("estado", "activo").execute()
			clientes_total = supabase.table("clientes").select("id").execute()
			
			candidatos_count = len(personal_activo.data) if personal_activo.data else 0
			proyectos_count = len(proyectos_activos.data) if proyectos_activos.data else 0
			clientes_count = len(clientes_total.data) if clientes_total.data else 0
		except Exception as e:
			candidatos_count = 0
			proyectos_count = 0
			clientes_count = 0
	else:
		candidatos_count = 0
		proyectos_count = 0
		clientes_count = 0
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.metric("Candidatos Activos", candidatos_count)
	
	with col2:
		st.metric("Proyectos Activos", proyectos_count)
	
	with col3:
		st.metric("Clientes", clientes_count)
	
	st.markdown("---")
	
	# Mostrar proyectos que terminan en menos de 30 días y profesionales que quedarán libres
	if init_clients():
		supabase = st.session_state.supabase
		
		try:
			# Calcular fechas: hoy y dentro de 30 días
			hoy = date.today()
			fecha_limite = hoy + timedelta(days=30)
			
			# Obtener proyectos que terminan en menos de 30 días
			proyectos_response = supabase.table("proyectos").select("id, nombre, fecha_fin, estado").execute()
			proyectos = proyectos_response.data if proyectos_response.data else []
			
			# Filtrar proyectos que terminan en menos de 30 días y están activos
			proyectos_por_terminar = []
			proyectos_ids = []
			
			for proyecto in proyectos:
				if proyecto.get('fecha_fin') and proyecto.get('estado') == 'activo':
					try:
						fecha_fin = datetime.strptime(proyecto['fecha_fin'], '%Y-%m-%d').date()
						if hoy <= fecha_fin <= fecha_limite:
							dias_restantes = (fecha_fin - hoy).days
							proyectos_por_terminar.append({
								**proyecto,
								'dias_restantes': dias_restantes
							})
							proyectos_ids.append(proyecto['id'])
					except (ValueError, TypeError):
						continue
			
			# Ordenar por días restantes (menos días primero)
			proyectos_por_terminar.sort(key=lambda x: x['dias_restantes'])
			
			# Obtener profesionales asignados a esos proyectos
			profesionales_libres = []
			if proyectos_ids:
				personal_response = supabase.table("personal").select(
					"id, nombre, apellido, rut, carrera_estudios, proyecto_id, proyectos(nombre, fecha_fin)"
				).in_("proyecto_id", proyectos_ids).eq("activo", True).execute()
				
				personal_list = personal_response.data if personal_response.data else []
				
				for persona in personal_list:
					# Manejar la relación con proyectos (puede ser objeto o None)
					proyecto_info = persona.get('proyectos')
					if proyecto_info:
						# Si es una lista (no debería serlo, pero por seguridad)
						if isinstance(proyecto_info, list) and len(proyecto_info) > 0:
							proyecto_info = proyecto_info[0]
						
						if proyecto_info and proyecto_info.get('fecha_fin'):
							try:
								fecha_fin = datetime.strptime(proyecto_info['fecha_fin'], '%Y-%m-%d').date()
								dias_restantes = (fecha_fin - hoy).days
								profesionales_libres.append({
									'nombre': persona.get('nombre', ''),
									'apellido': persona.get('apellido', ''),
									'rut': persona.get('rut', ''),
									'carrera_estudios': persona.get('carrera_estudios', 'N/A') or 'N/A',
									'proyecto_actual': proyecto_info.get('nombre', 'N/A'),
									'dias_restantes': dias_restantes
								})
							except (ValueError, TypeError):
								continue
				
				# Ordenar por días restantes (menos días primero)
				profesionales_libres.sort(key=lambda x: x['dias_restantes'])
			
			# Mostrar en dos columnas
			col1, col2 = st.columns(2)
			
			with col1:
				st.markdown("### Proyectos por terminar en menos de 30 días")
				
				if proyectos_por_terminar:
					for proyecto in proyectos_por_terminar:
						with st.container():
							st.markdown(f"""
							<div style="background-color: rgba(100, 181, 246, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #64b5f6;">
								<h4 style="color: #64b5f6; margin-bottom: 8px;">{proyecto.get('nombre', 'N/A')}</h4>
								<p style="color: #ffffff; margin: 0;">
									<strong>Días restantes:</strong> {proyecto['dias_restantes']} días<br>
									<strong>Fecha de término:</strong> {proyecto.get('fecha_fin', 'N/A')}
								</p>
							</div>
							""", unsafe_allow_html=True)
				else:
					st.info("No hay proyectos que terminen en los próximos 30 días")
			
			with col2:
				st.markdown("### Profesionales que quedarán libres")
				
				if profesionales_libres:
					for profesional in profesionales_libres:
						with st.container():
							st.markdown(f"""
							<div style="background-color: rgba(100, 181, 246, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #64b5f6;">
								<h4 style="color: #64b5f6; margin-bottom: 8px;">{profesional['nombre']} {profesional['apellido']}</h4>
								<p style="color: #ffffff; margin: 0; font-size: 0.9em;">
									<strong>RUT:</strong> {profesional['rut']}<br>
									<strong>Estudios:</strong> {profesional['carrera_estudios'][:50]}{'...' if len(profesional['carrera_estudios']) > 50 else ''}<br>
									<strong>Proyecto actual:</strong> {profesional['proyecto_actual']}<br>
									<strong>Días para estar libre:</strong> {profesional['dias_restantes']} días
								</p>
							</div>
							""", unsafe_allow_html=True)
				else:
					st.info("No hay profesionales que quedarán libres en los próximos 30 días")
		
		except Exception as e:
			st.error(f"Error al cargar información: {str(e)}")
			st.info("No se pudo cargar la información de proyectos y profesionales")

# Página de Carga de CVs
def page_cargar_cv():
	st.title("Cargar Curriculum Vitae")
	
	if not init_clients():
		return
	
	st.markdown("### Sube uno o múltiples CVs en formato PDF o DOCX para procesarlos automáticamente")
	
	# Opción para carga individual o masiva
	modo_carga = st.radio(
		"Modo de carga",
		["Carga Individual", "Carga Masiva"],
		horizontal=True
	)
	
	if modo_carga == "Carga Individual":
		uploaded_files = st.file_uploader(
			"Selecciona un archivo",
			type=["pdf", "docx"],
			help="Formatos soportados: PDF y DOCX",
			accept_multiple_files=False
		)
		uploaded_files_list = [uploaded_files] if uploaded_files else []
	else:
		uploaded_files_list = st.file_uploader(
			"Selecciona uno o más archivos",
			type=["pdf", "docx"],
			help="Formatos soportados: PDF y DOCX. Puedes seleccionar múltiples archivos a la vez.",
			accept_multiple_files=True
		)
	
	# Procesar archivos según el modo seleccionado
	if uploaded_files_list and len(uploaded_files_list) > 0:
		if modo_carga == "Carga Masiva" and len(uploaded_files_list) > 1:
			# Carga masiva: procesar todos los archivos automáticamente
			process_multiple_cvs(uploaded_files_list)
		else:
			# Carga individual: mostrar formulario de edición
			process_single_cv(uploaded_files_list[0])

# Función para procesar múltiples CVs (carga masiva)
def process_multiple_cvs(uploaded_files_list):
	"""Procesa múltiples CVs de forma automática y los guarda en la base de datos"""
	st.markdown(f"### Procesando {len(uploaded_files_list)} CVs...")
	
	# Crear contenedor para mostrar progreso
	progress_container = st.container()
	
	# Contadores para estadísticas
	success_count = 0
	error_count = 0
	skipped_count = 0
	
	# Procesar cada archivo
	for idx, uploaded_file in enumerate(uploaded_files_list, 1):
		with progress_container:
			st.markdown(f"---")
			st.markdown(f"**CV {idx}/{len(uploaded_files_list)}: {uploaded_file.name}**")
			
			with st.spinner(f"Procesando {uploaded_file.name}..."):
				try:
					# Extraer texto según el tipo de archivo
					if uploaded_file.type == "application/pdf":
						cv_text = extract_text_from_pdf(uploaded_file)
					elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
						cv_text = extract_text_from_docx(uploaded_file)
					else:
						st.error(f"❌ Formato no soportado: {uploaded_file.name}")
						error_count += 1
						continue
					
					if not cv_text:
						st.error(f"❌ No se pudo extraer texto de: {uploaded_file.name}")
						error_count += 1
						continue
					
					# Procesar con IA
					processed_data = process_cv_with_ai(cv_text)
					
					if not processed_data:
						st.error(f"❌ Error al procesar con IA: {uploaded_file.name}")
						error_count += 1
						continue
					
					# Validar datos mínimos
					rut_normalized = normalize_rut(processed_data.get("rut"))
					nombre = processed_data.get("nombre", "").strip()
					apellido = processed_data.get("apellido", "").strip()
					
					if not rut_normalized or not nombre or not apellido:
						st.warning(f"⚠️ Datos incompletos (RUT, Nombre o Apellido faltantes): {uploaded_file.name}")
						skipped_count += 1
						continue
					
					# Preparar datos para guardar
					personal_data = {
						"rut": rut_normalized,
						"nombre": nombre,
						"apellido": apellido,
						"telefono_personal": processed_data.get("telefono_personal"),
						"correo_personal": processed_data.get("correo_personal"),
						"carrera_estudios": processed_data.get("carrera_estudios"),
						"experiencia": processed_data.get("experiencia"),
						"anos_experiencia": processed_data.get("anos_experiencia"),
						"certificaciones": processed_data.get("certificaciones"),
						"otros": processed_data.get("otros"),
						"resumen_ia": processed_data.get("resumen_ia")
					}
					
					# Subir CV a Storage
					cv_url = None
					file_extension = "pdf" if uploaded_file.type == "application/pdf" else "docx"
					cv_url = upload_cv_to_storage(uploaded_file, rut_normalized, file_extension)
					
					# Guardar en base de datos
					if save_personal_to_db(personal_data, cv_url):
						st.success(f"✅ {nombre} {apellido} (RUT: {rut_normalized}) - Guardado exitosamente")
						success_count += 1
					else:
						st.error(f"❌ Error al guardar: {uploaded_file.name}")
						error_count += 1
					
				except Exception as e:
					st.error(f"❌ Error procesando {uploaded_file.name}: {str(e)}")
					error_count += 1
	
	# Mostrar resumen final
	st.markdown("---")
	st.markdown("### 📊 Resumen del Procesamiento")
	col1, col2, col3 = st.columns(3)
	with col1:
		st.metric("✅ Exitosos", success_count)
	with col2:
		st.metric("❌ Errores", error_count)
	with col3:
		st.metric("⚠️ Omitidos", skipped_count)
	
	if success_count > 0:
		st.success(f"🎉 Se procesaron y guardaron exitosamente {success_count} CV(s)")

# Función para procesar un solo CV (modo individual con edición)
def process_single_cv(uploaded_file):
	"""Procesa un solo CV y permite edición antes de guardar"""
	with st.spinner("Procesando CV..."):
		# Extraer texto según el tipo de archivo
		if uploaded_file.type == "application/pdf":
			cv_text = extract_text_from_pdf(uploaded_file)
		elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
			cv_text = extract_text_from_docx(uploaded_file)
		else:
			st.error("Formato de archivo no soportado")
			return
		
		if not cv_text:
			st.error("No se pudo extraer texto del archivo")
			return
		
		# Mostrar texto extraído (opcional, en un expander)
		with st.expander("Ver texto extraído del CV"):
			st.text(cv_text[:2000])  # Mostrar primeros 2000 caracteres
		
		# Procesar con IA
		st.info("🤖 Procesando con IA...")
		processed_data = process_cv_with_ai(cv_text)
		
		if processed_data:
			st.success("✅ CV procesado exitosamente")
			
			# Mostrar datos extraídos
			st.markdown("### Información Extraída:")
			
			col1, col2 = st.columns(2)
			
			with col1:
				st.text_input("RUT", value=processed_data.get("rut", ""), disabled=True)
				st.text_input("Nombre", value=processed_data.get("nombre", ""), disabled=True)
				st.text_input("Apellido", value=processed_data.get("apellido", ""), disabled=True)
				st.text_input("Teléfono", value=processed_data.get("telefono_personal", ""), disabled=True)
				st.text_input("Correo", value=processed_data.get("correo_personal", ""), disabled=True)
			
				with col2:
					st.text_area("Carrera/Estudios", value=processed_data.get("carrera_estudios", ""), disabled=True, height=100)
					st.number_input("Años de Experiencia", value=processed_data.get("anos_experiencia") or 0, disabled=True)
					st.text_area("Experiencia", value=processed_data.get("experiencia", ""), disabled=True, height=100)
				
				if processed_data.get("certificaciones"):
					st.text_area("Certificaciones", value=processed_data.get("certificaciones", ""), disabled=True, height=100)
				
				st.text_area("Resumen IA", value=processed_data.get("resumen_ia", ""), disabled=True, height=150)
				
				if processed_data.get("otros"):
					st.text_area("Otros", value=processed_data.get("otros", ""), disabled=True, height=100)
			
			# Permitir edición antes de guardar
			st.markdown("### Editar información antes de guardar:")
			
			edited_data = {
				"rut": st.text_input(
					"RUT sin puntos, guiones ni dígito verificador *", 
					value=processed_data.get("rut", ""), 
					key="edit_rut",
					help="Se guardará solo con los primeros 8 dígitos (sin puntos, guiones ni dígito verificador)"
				),
				"nombre": st.text_input("Nombre *", value=processed_data.get("nombre", ""), key="edit_nombre"),
				"apellido": st.text_input("Apellido *", value=processed_data.get("apellido", ""), key="edit_apellido"),
				"telefono_personal": st.text_input("Teléfono Personal", value=processed_data.get("telefono_personal", ""), key="edit_telefono"),
				"correo_personal": st.text_input("Correo Personal", value=processed_data.get("correo_personal", ""), key="edit_correo"),
				"carrera_estudios": st.text_area("Carrera/Estudios", value=processed_data.get("carrera_estudios", ""), key="edit_carrera"),
				"experiencia": st.text_area("Experiencia", value=processed_data.get("experiencia", ""), key="edit_experiencia"),
				"anos_experiencia": st.number_input("Años de Experiencia", value=processed_data.get("anos_experiencia") or 0, min_value=0, key="edit_anos"),
				"certificaciones": st.text_area("Certificaciones", value=processed_data.get("certificaciones", ""), key="edit_certificaciones"),
				"otros": st.text_area("Otros", value=processed_data.get("otros", ""), key="edit_otros"),
				"resumen_ia": st.text_area("Resumen IA", value=processed_data.get("resumen_ia", ""), key="edit_resumen")
			}
			
			if st.button("💾 Guardar en Base de Datos", type="primary"):
				if edited_data["rut"] and edited_data["nombre"] and edited_data["apellido"]:
					# Subir CV a Storage antes de guardar
					cv_url = None
					if uploaded_file is not None:
						with st.spinner("📤 Subiendo CV a Storage..."):
							file_extension = "pdf" if uploaded_file.type == "application/pdf" else "docx"
							cv_url = upload_cv_to_storage(uploaded_file, edited_data["rut"], file_extension)
							if cv_url:
								st.success("✅ CV subido exitosamente")
							else:
								st.warning("⚠️ No se pudo subir el CV, pero se guardará la información")
					
					if save_personal_to_db(edited_data, cv_url):
						st.success("✅ Personal guardado exitosamente en la base de datos")
						if cv_url:
							st.info(f"📄 CV disponible en: {cv_url}")
					else:
						st.error("❌ Error al guardar en la base de datos")
				else:
					st.warning("⚠️ Por favor completa los campos obligatorios (RUT, Nombre, Apellido)")

# Página de Búsqueda de Candidatos
def page_buscar_candidatos():
	st.title("Buscar Candidatos")
	
	if not init_clients():
		return
	
	st.markdown("### Describe los requerimientos del puesto y encuentra los mejores candidatos")
	
	description = st.text_area(
		"Descripción del puesto o requerimientos",
		height=200,
		placeholder="Ejemplo: Necesito un ingeniero civil con experiencia en inspecciones técnicas de obras, mínimo 5 años de experiencia, conocimientos en normativas de construcción..."
	)
	
	if st.button("🔍 Buscar Candidatos", type="primary"):
		if description:
			with st.spinner("Buscando candidatos con IA..."):
				candidates = search_candidates_with_ai(description)
				
				if candidates:
					st.success(f"✅ Se encontraron {len(candidates)} candidatos")
					
					for idx, candidate in enumerate(candidates, 1):
						with st.expander(f"#{idx} - {candidate.get('nombre', '')} {candidate.get('apellido', '')} - RUT: {candidate.get('rut', '')}"):
							col1, col2 = st.columns(2)
							
							with col1:
								st.markdown(f"**RUT:** {candidate.get('rut', 'N/A')}")
								st.markdown(f"**Nombre:** {candidate.get('nombre', '')} {candidate.get('apellido', '')}")
								st.markdown(f"**Teléfono:** {candidate.get('telefono_personal', 'N/A')}")
								st.markdown(f"**Correo:** {candidate.get('correo_personal', 'N/A')}")
								st.markdown(f"**Años de Experiencia:** {candidate.get('anos_experiencia', 'N/A')}")
							
							with col2:
								st.markdown(f"**Carrera/Estudios:** {candidate.get('carrera_estudios', 'N/A')}")
								st.markdown(f"**Activo:** {'Sí' if candidate.get('activo') else 'No'}")
								st.markdown(f"**Contratado:** {'Sí' if candidate.get('contratado') else 'No'}")
								puntuacion = candidate.get('puntuacion_calidad')
								if puntuacion:
									estrellas = "⭐" * puntuacion
									st.markdown(f"**Puntuación de Calidad:** {estrellas} ({puntuacion}/5)")
								else:
									st.markdown(f"**Puntuación de Calidad:** Sin puntuación")
								if candidate.get('proyecto_id'):
									st.markdown(f"**Proyecto Asignado:** {candidate.get('proyecto_id')}")
							
							# Visualización del CV
							if candidate.get('cv_url'):
								st.markdown("---")
								st.markdown("### 📄 Curriculum Vitae")
								cv_url = candidate.get('cv_url')
								
								if cv_url.endswith('.pdf'):
									st.markdown(f"**Ver CV:** [Abrir PDF en nueva pestaña]({cv_url})")
									try:
										st.components.v1.iframe(cv_url, height=600, scrolling=True)
									except:
										st.markdown(f"[Descargar PDF]({cv_url})")
								elif cv_url.endswith('.docx'):
									st.markdown(f"**Descargar CV:** [Descargar DOCX]({cv_url})")
									st.info("💡 Los archivos DOCX deben descargarse para visualizarlos")
								else:
									st.markdown(f"**Ver CV:** [Abrir archivo]({cv_url})")
							
							if candidate.get('experiencia'):
								st.markdown(f"**Experiencia:**\n{candidate.get('experiencia')}")
							
							if candidate.get('certificaciones'):
								st.markdown(f"**Certificaciones:**\n{candidate.get('certificaciones')}")
							
							if candidate.get('resumen_ia'):
								st.markdown(f"**Resumen IA:**\n{candidate.get('resumen_ia')}")
							
							if candidate.get('otros'):
								st.markdown(f"**Otros:**\n{candidate.get('otros')}")
				else:
					st.warning("No se encontraron candidatos que coincidan con los criterios")
		else:
			st.warning("Por favor ingresa una descripción del puesto")

# Página de Gestión de Personal
def page_gestionar_personal():
	st.title("Gestionar Personal")
	
	if not init_clients():
		return
	
	supabase = st.session_state.supabase
	
	# Opciones
	tab1, tab2 = st.tabs(["Ver Personal", "Editar Personal"])
	
	with tab1:
		st.markdown("### Lista de Personal")
		
		# Filtros
		col1, col2, col3 = st.columns(3)
		with col1:
			filter_activo = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"])
		with col2:
			filter_contratado = st.selectbox("Contratado", ["Todos", "Sí", "No"])
		with col3:
			search_term = st.text_input("Buscar por nombre o RUT")
		
		# Obtener personal
		query = supabase.table("personal").select("*")
		
		if filter_activo == "Activos":
			query = query.eq("activo", True)
		elif filter_activo == "Inactivos":
			query = query.eq("activo", False)
		
		if filter_contratado == "Sí":
			query = query.eq("contratado", True)
		elif filter_contratado == "No":
			query = query.eq("contratado", False)
		
		response = query.execute()
		personal_list = response.data
		
		# Filtrar por término de búsqueda
		if search_term:
			personal_list = [
				p for p in personal_list
				if search_term.lower() in p.get('nombre', '').lower() or
				search_term.lower() in p.get('apellido', '').lower() or
				search_term.lower() in p.get('rut', '').lower()
			]
		
		if personal_list:
			st.info(f"Total: {len(personal_list)} registros")
			
			for person in personal_list:
				with st.expander(f"{person.get('nombre', '')} {person.get('apellido', '')} - RUT: {person.get('rut', '')}"):
					col1, col2 = st.columns(2)
					
					with col1:
						st.markdown(f"**RUT:** {person.get('rut', 'N/A')}")
						st.markdown(f"**Nombre:** {person.get('nombre', '')} {person.get('apellido', '')}")
						st.markdown(f"**Teléfono:** {person.get('telefono_personal', 'N/A')}")
						st.markdown(f"**Correo:** {person.get('correo_personal', 'N/A')}")
						st.markdown(f"**Años de Experiencia:** {person.get('anos_experiencia', 'N/A')}")
					
					with col2:
						st.markdown(f"**Carrera/Estudios:** {person.get('carrera_estudios', 'N/A')}")
						st.markdown(f"**Activo:** {'Sí' if person.get('activo') else 'No'}")
						st.markdown(f"**Contratado:** {'Sí' if person.get('contratado') else 'No'}")
						puntuacion = person.get('puntuacion_calidad')
						if puntuacion:
							estrellas = "⭐" * puntuacion
							st.markdown(f"**Puntuación de Calidad:** {estrellas} ({puntuacion}/5)")
						else:
							st.markdown(f"**Puntuación de Calidad:** Sin puntuación")
						if person.get('proyecto_id'):
							st.markdown(f"**Proyecto ID:** {person.get('proyecto_id')}")
					
					# Visualización del CV
					if person.get('cv_url'):
						st.markdown("---")
						st.markdown("### 📄 Curriculum Vitae")
						cv_url = person.get('cv_url')
						
						# Determinar si es PDF o DOCX para mostrar correctamente
						if cv_url.endswith('.pdf'):
							st.markdown(f"**Ver CV:** [Abrir PDF en nueva pestaña]({cv_url})")
							# Mostrar PDF embebido si es posible
							try:
								st.components.v1.iframe(cv_url, height=600, scrolling=True)
							except:
								st.markdown(f"[Descargar PDF]({cv_url})")
						elif cv_url.endswith('.docx'):
							st.markdown(f"**Descargar CV:** [Descargar DOCX]({cv_url})")
							st.info("💡 Los archivos DOCX deben descargarse para visualizarlos")
						else:
							st.markdown(f"**Ver CV:** [Abrir archivo]({cv_url})")
					else:
						st.info("ℹ️ No hay CV disponible para esta persona")
					
					if person.get('experiencia'):
						st.markdown(f"**Experiencia:**\n{person.get('experiencia')}")
					
					if person.get('certificaciones'):
						st.markdown(f"**Certificaciones:**\n{person.get('certificaciones')}")
					
					if person.get('resumen_ia'):
						st.markdown(f"**Resumen IA:**\n{person.get('resumen_ia')}")
		else:
			st.info("No se encontró personal con los filtros seleccionados")
	
	with tab2:
		st.markdown("### Editar Personal")
		
		# Obtener lista de personal para seleccionar
		response = supabase.table("personal").select("id, nombre, apellido, rut").execute()
		personal_options = response.data
		
		if personal_options:
			person_options_dict = {f"{p['nombre']} {p['apellido']} - {p['rut']}": p['id'] for p in personal_options}
			selected_person = st.selectbox("Selecciona una persona", list(person_options_dict.keys()))
			
			if selected_person:
				person_id = person_options_dict[selected_person]
				person_data = supabase.table("personal").select("*").eq("id", person_id).execute().data[0]
				
				# Mostrar CV si está disponible
				if person_data.get('cv_url'):
					st.markdown("### 📄 Curriculum Vitae")
					cv_url = person_data.get('cv_url')
					
					if cv_url.endswith('.pdf'):
						st.markdown(f"**Ver CV:** [Abrir PDF en nueva pestaña]({cv_url})")
						try:
							st.components.v1.iframe(cv_url, height=600, scrolling=True)
						except:
							st.markdown(f"[Descargar PDF]({cv_url})")
					elif cv_url.endswith('.docx'):
						st.markdown(f"**Descargar CV:** [Descargar DOCX]({cv_url})")
						st.info("💡 Los archivos DOCX deben descargarse para visualizarlos")
					else:
						st.markdown(f"**Ver CV:** [Abrir archivo]({cv_url})")
					
					st.markdown("---")
				
				# Obtener proyectos para asignar
				proyectos_response = supabase.table("proyectos").select("id, nombre").execute()
				proyectos_options = {p['nombre']: p['id'] for p in proyectos_response.data}
				proyectos_options["Sin proyecto"] = None
				
				# Formulario de edición
				with st.form("edit_personal_form"):
					col1, col2 = st.columns(2)
					
					with col1:
						edit_rut = st.text_input(
							"RUT", 
							value=person_data.get('rut', ''),
							help="Se guardará solo con los primeros 8 dígitos (sin puntos, guiones ni dígito verificador)"
						)
						edit_nombre = st.text_input("Nombre", value=person_data.get('nombre', ''))
						edit_apellido = st.text_input("Apellido", value=person_data.get('apellido', ''))
						edit_telefono = st.text_input("Teléfono", value=person_data.get('telefono_personal', ''))
						edit_correo = st.text_input("Correo", value=person_data.get('correo_personal', ''))
					
					with col2:
						edit_carrera = st.text_area("Carrera/Estudios", value=person_data.get('carrera_estudios', ''))
						edit_experiencia = st.text_area("Experiencia", value=person_data.get('experiencia', ''))
						edit_anos = st.number_input("Años de Experiencia", value=person_data.get('anos_experiencia') or 0, min_value=0)
						edit_certificaciones = st.text_area("Certificaciones", value=person_data.get('certificaciones', ''), help="Certificaciones, licencias, cursos o capacitaciones profesionales")
						edit_otros = st.text_area("Otros", value=person_data.get('otros', ''))
					
					edit_resumen = st.text_area("Resumen IA", value=person_data.get('resumen_ia', ''), height=150)
					
					col3, col4, col5 = st.columns(3)
					with col3:
						edit_activo = st.checkbox("Activo", value=person_data.get('activo', True))
					with col4:
						edit_contratado = st.checkbox("Contratado", value=person_data.get('contratado', False))
					with col5:
						# Determinar el índice del proyecto seleccionado
						proyecto_keys = list(proyectos_options.keys())
						proyecto_index = 0
						if person_data.get('proyecto_id'):
							for key, value in proyectos_options.items():
								if value == person_data.get('proyecto_id'):
									proyecto_index = proyecto_keys.index(key)
									break
						selected_proyecto = st.selectbox("Proyecto", proyecto_keys, index=proyecto_index)
					
					# Sistema de puntuación de calidad (1-5 estrellas)
					st.markdown("---")
					st.markdown("### ⭐ Puntuación de Calidad")
					puntuacion_opciones = {
						"Sin puntuación": None,
						"⭐ (1 estrella)": 1,
						"⭐⭐ (2 estrellas)": 2,
						"⭐⭐⭐ (3 estrellas)": 3,
						"⭐⭐⭐⭐ (4 estrellas)": 4,
						"⭐⭐⭐⭐⭐ (5 estrellas)": 5
					}
					
					# Determinar el índice de la puntuación actual
					puntuacion_actual = person_data.get('puntuacion_calidad')
					puntuacion_index = 0
					if puntuacion_actual:
						for key, value in puntuacion_opciones.items():
							if value == puntuacion_actual:
								puntuacion_index = list(puntuacion_opciones.keys()).index(key)
								break
					
					selected_puntuacion = st.selectbox(
						"Calidad del trabajo (1-5 estrellas)",
						options=list(puntuacion_opciones.keys()),
						index=puntuacion_index,
						help="Evalúa la calidad del trabajo de esta persona. Esta puntuación será considerada al buscar candidatos."
					)
					
					if st.form_submit_button("💾 Guardar Cambios", type="primary"):
						# Normalizar RUT antes de guardar
						rut_normalized = normalize_rut(edit_rut)
						
						update_data = {
							"rut": rut_normalized,  # RUT normalizado (solo primeros 8 dígitos)
							"nombre": edit_nombre,
							"apellido": edit_apellido,
							"telefono_personal": edit_telefono,
							"correo_personal": edit_correo,
							"carrera_estudios": edit_carrera,
							"experiencia": edit_experiencia,
							"anos_experiencia": edit_anos,
							"certificaciones": edit_certificaciones,
							"otros": edit_otros,
							"resumen_ia": edit_resumen,
							"activo": edit_activo,
							"contratado": edit_contratado,
							"proyecto_id": proyectos_options[selected_proyecto],
							"puntuacion_calidad": puntuacion_opciones[selected_puntuacion],
							"updated_at": datetime.now().isoformat()
						}
						
						try:
							supabase.table("personal").update(update_data).eq("id", person_id).execute()
							st.success("✅ Personal actualizado exitosamente")
							st.rerun()
						except Exception as e:
							st.error(f"Error al actualizar: {str(e)}")
		else:
			st.info("No hay personal registrado para editar")

# Página de Gestión de Proyectos
def page_gestionar_proyectos():
	st.title("Gestionar Proyectos")
	
	if not init_clients():
		return
	
	supabase = st.session_state.supabase
	
	tab1, tab2 = st.tabs(["Ver Proyectos", "Crear/Editar Proyecto"])
	
	with tab1:
		st.markdown("### Lista de Proyectos")
		
		response = supabase.table("proyectos").select("*, clientes(*)").execute()
		proyectos = response.data
		
		if proyectos:
			for proyecto in proyectos:
				cliente_nombre = proyecto.get('clientes', {}).get('nombre', 'N/A') if proyecto.get('clientes') else 'N/A'
				
				with st.expander(f"{proyecto.get('nombre', '')} - Cliente: {cliente_nombre}"):
					col1, col2 = st.columns(2)
					
					with col1:
						st.markdown(f"**Nombre:** {proyecto.get('nombre', 'N/A')}")
						st.markdown(f"**Cliente:** {cliente_nombre}")
						st.markdown(f"**Estado:** {proyecto.get('estado', 'N/A')}")
					
					with col2:
						st.markdown(f"**Fecha Inicio:** {proyecto.get('fecha_inicio', 'N/A')}")
						st.markdown(f"**Fecha Fin:** {proyecto.get('fecha_fin', 'N/A')}")
					
					if proyecto.get('descripcion'):
						st.markdown(f"**Descripción:**\n{proyecto.get('descripcion')}")
		else:
			st.info("No hay proyectos registrados")
	
	with tab2:
		st.markdown("### Crear o Editar Proyecto")
		
		# Obtener clientes
		clientes_response = supabase.table("clientes").select("id, nombre").execute()
		clientes_options = {c['nombre']: c['id'] for c in clientes_response.data}
		clientes_options["Sin cliente"] = None
		
		# Opción para editar proyecto existente
		proyectos_response = supabase.table("proyectos").select("id, nombre").execute()
		proyectos_list = proyectos_response.data
		
		edit_mode = st.checkbox("Editar proyecto existente")
		
		if edit_mode and proyectos_list:
			proyecto_options_dict = {f"{p['nombre']}": p['id'] for p in proyectos_list}
			selected_proyecto = st.selectbox("Selecciona un proyecto", list(proyecto_options_dict.keys()))
			proyecto_id = proyecto_options_dict[selected_proyecto]
			proyecto_data = supabase.table("proyectos").select("*").eq("id", proyecto_id).execute().data[0]
		else:
			proyecto_data = {}
			proyecto_id = None
		
		with st.form("proyecto_form"):
			nombre = st.text_input("Nombre del Proyecto *", value=proyecto_data.get('nombre', ''))
			descripcion = st.text_area("Descripción", value=proyecto_data.get('descripcion', ''))
			
			col1, col2, col3 = st.columns(3)
			with col1:
				# Determinar el índice del cliente seleccionado
				cliente_keys = list(clientes_options.keys())
				cliente_index = 0
				if proyecto_data.get('cliente_id'):
					for key, value in clientes_options.items():
						if value == proyecto_data.get('cliente_id'):
							cliente_index = cliente_keys.index(key)
							break
				cliente_selected = st.selectbox("Cliente", cliente_keys, index=cliente_index)
			with col2:
				fecha_inicio = st.date_input("Fecha Inicio", value=datetime.fromisoformat(proyecto_data.get('fecha_inicio')).date() if proyecto_data.get('fecha_inicio') else None)
			with col3:
				fecha_fin = st.date_input("Fecha Fin", value=datetime.fromisoformat(proyecto_data.get('fecha_fin')).date() if proyecto_data.get('fecha_fin') else None)
			
			estado = st.selectbox("Estado", ["activo", "completado", "pausado", "cancelado"],
				index=["activo", "completado", "pausado", "cancelado"].index(proyecto_data.get('estado', 'activo')) if proyecto_data.get('estado') else 0)
			
			if st.form_submit_button("💾 Guardar Proyecto", type="primary"):
				if nombre:
					proyecto_data_to_save = {
						"nombre": nombre,
						"descripcion": descripcion,
						"cliente_id": clientes_options[cliente_selected],
						"fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
						"fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
						"estado": estado,
						"updated_at": datetime.now().isoformat()
					}
					
					try:
						if proyecto_id:
							supabase.table("proyectos").update(proyecto_data_to_save).eq("id", proyecto_id).execute()
							st.success("✅ Proyecto actualizado exitosamente")
						else:
							supabase.table("proyectos").insert(proyecto_data_to_save).execute()
							st.success("✅ Proyecto creado exitosamente")
						st.rerun()
					except Exception as e:
						st.error(f"Error al guardar proyecto: {str(e)}")
				else:
					st.warning("Por favor ingresa un nombre para el proyecto")

# Página de Gestión de Clientes
def page_gestionar_clientes():
	st.title("Gestionar Clientes")
	
	if not init_clients():
		return
	
	supabase = st.session_state.supabase
	
	tab1, tab2 = st.tabs(["Ver Clientes", "Crear/Editar Cliente"])
	
	with tab1:
		st.markdown("### Lista de Clientes")
		
		response = supabase.table("clientes").select("*").execute()
		clientes = response.data
		
		if clientes:
			for cliente in clientes:
				with st.expander(f"{cliente.get('nombre', '')} - RUT: {cliente.get('rut', 'N/A')}"):
					col1, col2 = st.columns(2)
					
					with col1:
						st.markdown(f"**Nombre:** {cliente.get('nombre', 'N/A')}")
						st.markdown(f"**RUT:** {cliente.get('rut', 'N/A')}")
						st.markdown(f"**Correo:** {cliente.get('correo', 'N/A')}")
					
					with col2:
						st.markdown(f"**Teléfono:** {cliente.get('telefono', 'N/A')}")
						st.markdown(f"**Dirección:** {cliente.get('direccion', 'N/A')}")
		else:
			st.info("No hay clientes registrados")
	
	with tab2:
		st.markdown("### Crear o Editar Cliente")
		
		# Opción para editar cliente existente
		clientes_response = supabase.table("clientes").select("id, nombre, rut").execute()
		clientes_list = clientes_response.data
		
		edit_mode = st.checkbox("Editar cliente existente")
		
		if edit_mode and clientes_list:
			cliente_options_dict = {f"{c['nombre']} - {c['rut']}": c['id'] for c in clientes_list}
			selected_cliente = st.selectbox("Selecciona un cliente", list(cliente_options_dict.keys()))
			cliente_id = cliente_options_dict[selected_cliente]
			cliente_data = supabase.table("clientes").select("*").eq("id", cliente_id).execute().data[0]
		else:
			cliente_data = {}
			cliente_id = None
		
		with st.form("cliente_form"):
			col1, col2 = st.columns(2)
			
			with col1:
				nombre = st.text_input("Nombre *", value=cliente_data.get('nombre', ''))
				rut = st.text_input("RUT", value=cliente_data.get('rut', ''))
				correo = st.text_input("Correo", value=cliente_data.get('correo', ''))
			
			with col2:
				telefono = st.text_input("Teléfono", value=cliente_data.get('telefono', ''))
				direccion = st.text_area("Dirección", value=cliente_data.get('direccion', ''))
			
			if st.form_submit_button("💾 Guardar Cliente", type="primary"):
				if nombre:
					cliente_data_to_save = {
						"nombre": nombre,
						"rut": rut if rut else None,
						"correo": correo if correo else None,
						"telefono": telefono if telefono else None,
						"direccion": direccion if direccion else None,
						"updated_at": datetime.now().isoformat()
					}
					
					try:
						if cliente_id:
							supabase.table("clientes").update(cliente_data_to_save).eq("id", cliente_id).execute()
							st.success("✅ Cliente actualizado exitosamente")
						else:
							supabase.table("clientes").insert(cliente_data_to_save).execute()
							st.success("✅ Cliente creado exitosamente")
						st.rerun()
					except Exception as e:
						st.error(f"Error al guardar cliente: {str(e)}")
				else:
					st.warning("Por favor ingresa un nombre para el cliente")

# Navegación principal
def main():
	# Sidebar navigation
	with st.sidebar:
		# Logo de TPF Ingeniería - Mostrar imagen sin procesar
		logo_path = "logo_tpf.png"  # Cambia esto por la ruta de tu logo si lo tienes
		if os.path.exists(logo_path):
			st.image(logo_path)
		else:
			# Logo SVG estilizado con cubo geométrico
			st.markdown("""
				<div class="logo-container">
					<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
						<defs>
							<linearGradient id="cubeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" style="stop-color:#0066CC;stop-opacity:0.8" />
								<stop offset="50%" style="stop-color:#4fc3f7;stop-opacity:0.6" />
								<stop offset="100%" style="stop-color:#87ceeb;stop-opacity:0.4" />
							</linearGradient>
						</defs>
						<!-- Cubo geométrico 3D -->
						<polygon points="30,20 50,10 70,20 50,30" fill="url(#cubeGrad)" opacity="0.7"/>
						<polygon points="50,10 70,20 70,40 50,30" fill="url(#cubeGrad)" opacity="0.5"/>
						<polygon points="30,20 50,30 50,50 30,40" fill="url(#cubeGrad)" opacity="0.6"/>
						<!-- Texto TPF -->
						<text x="100" y="35" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="#87ceeb" text-anchor="start">TPF</text>
						<!-- Texto INGENIERÍA -->
						<text x="100" y="55" font-family="Arial, sans-serif" font-size="14" fill="#4fc3f7" text-anchor="start">INGENIERÍA</text>
					</svg>
				</div>
			""", unsafe_allow_html=True)
		st.markdown("---")
		
		page = st.radio(
			"Navegación",
			["Inicio", "Cargar CV", "Buscar Candidatos", "Gestionar Personal", "Gestionar Proyectos", "Gestionar Clientes"],
			label_visibility="collapsed"
		)
	
	# Renderizar página seleccionada
	if page == "Inicio":
		page_inicio()
	elif page == "Cargar CV":
		page_cargar_cv()
	elif page == "Buscar Candidatos":
		page_buscar_candidatos()
	elif page == "Gestionar Personal":
		page_gestionar_personal()
	elif page == "Gestionar Proyectos":
		page_gestionar_proyectos()
	elif page == "Gestionar Clientes":
		page_gestionar_clientes()

if __name__ == "__main__":
	main()

