# Scraper de Películas de IMDb con Scrapy

Este proyecto implementa un web scraper usando Scrapy para extraer información de las mejores películas de IMDb.

## Características

- **Framework**: Scrapy (framework profesional de web scraping)
- **Patrón Factory**: Implementación del patrón de diseño Factory
- **Manejo de errores**: Reintentos automáticos y manejo de WAF
- **Exportación dual**: CSV y base de datos PostgreSQL
- **Datos auténticos**: Fallback a datos reales de IMDb cuando el scraping es bloqueado

## Datos Extraídos

Para cada película se extrae:
- ✅ **Título**
- ✅ **Año de estreno**
- ✅ **Calificación** (IMDb rating)
- ✅ **Duración en minutos** (desde página de detalle)
- ✅ **Metascore** (si está disponible)
- ✅ **Al menos 3 actores principales**

## 📁 Estructura del Proyecto
```
imdb_movie_scraper/
├── imdb_scraper
├── app
│   ├── main.py
│   ├── db
│   ├── models
│   ├── queries
│   ├── routers
│   ├── scripts
│   └── utils
└── start.sh
├── data
├── docker-compose.db.yml
├── requirements.txt
├── runtime.txt
├── README.md
```

## 🚀 Instalación y Uso

1. **Clona el repositorio:**

```bash
git clone https://github.com/migherize/imdb-movie-scraper.git
cd imdb-movie-scraper
```

2. **Copia el archivo `.env`:**

```bash
cp .env.example .env
```

### ▶️ Opción 1: Sin Docker

1. **Crea y activa un entorno virtual:**

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. **Instala dependencias:**

```bash
pip install -r requirements.txt
```

---

### 🛢️ **Base de datos PostgreSQL (modo opcional)**

Si deseas usar PostgreSQL localmente (sin Docker), puedes crear la base de datos y sus tablas ejecutando el script `app/utils/schema.sql` incluido en el proyecto.

#### ✅ Pasos:

1. **Asegúrate de tener PostgreSQL instalado** y que el servicio esté en ejecución.

2. **Crea la base de datos manualmente** (si aún no existe):

   ```bash
   createdb imdb
   ```

3. **Ejecuta el script SQL para crear las tablas:**

   ```bash
   psql -h localhost -U tu_usuario -d imdb -f app/utils/schema.sql
   ```

   > Reemplaza `tu_usuario` por tu nombre de usuario en PostgreSQL.

#### 📄 ¿Qué incluye `schema.sql`?

Este archivo define la estructura base de la base de datos:

* `movies`: tabla con información de películas (título, año, duración, rating, metascore).
* `actors`: tabla que almacena los actores, asociados a las películas por la clave foránea `movie_id`.
* Índices y restricciones para mejorar la consulta.
* Creación de la vista `movie_actor_view` que relaciona películas con sus actores principales.

---

### 🐳 Opción 2: Uso con Docker

Puedes levantar la base de datos y el servicio completo usando Docker.

#### 1. Levantar la base de datos PostgreSQL:

```bash
docker-compose -f docker-compose.db.yml up --build
```

Esto construirá y levantará el contenedor `imdb-movie-scraper-db-1` con PostgreSQL.

---

#### 2. Copiar el archivo `schema.sql` al contenedor:

```bash
docker cp PYTHONPATH/app/utils/schema.sql imdb-movie-scraper-db-1:/schema.sql
```

> Asegúrate de ajustar la ruta al archivo según tu estructura local, si es necesario.

---

#### 3. Acceder al contenedor:

```bash
docker exec -it imdb-movie-scraper-db-1 bash
```

---

#### 4. Ejecutar el archivo `schema.sql` dentro del contenedor:

```bash
psql -h localhost -U user -d imdb -f schema.sql
```

> Reemplaza `user` y `imdb` por tu usuario y nombre de base de datos si son diferentes.
> Si necesitas contraseña, te la pedirá (`password`, según tu `.env`).

---

#### 2. 🔌 Levantar el servicio IMDB-MOVIE-SCRAPER (opcional)

Si deseas levantar toda la aplicación con FastAPI (incluyendo la base de datos y la API), ejecuta:

```bash
docker-compose -f docker-compose.yml up --build
```

Luego, dirígete a la sección [🚀 Usar la API con FastAPI (opcional)](#-usar-la-api-con-fastapi-opcional) para más detalles.

---

### ✅ Ejecutar los tests

1. Asegúrate de instalar las dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecuta las pruebas con `pytest`:

```bash
pytest
```

📸 Resultado esperado:

![test](docs/test.png)

> **Nota:** El test `test_database_has_data` puede fallar si la base de datos está vacía. Esto es normal si aún no has hecho el scraping de datos. El siguiente paso es ejecutar el scraper para poblar la base.

---
Claro, aquí tienes la sección completada con una redacción clara, profesional y consistente con el estilo del resto del README:

---

## 🎬 Web Scraper: IMDB Movies

Para poblar la base de datos con información de películas y actores:

```bash
cd imdb_scraper
scrapy crawl imdb_movies_spider
```

Si todo funciona correctamente, deberías ver el siguiente mensaje.

📸 Resultado esperado:

![FIN WEBSCRAPY](docs/WEBSCRAPY.png)

---

## 📊 Consultas SQL Avanzadas

Este proyecto incluye un conjunto de scripts para ejecutar análisis avanzados sobre la base de datos poblada desde IMDB.

Ejecuta los siguientes comandos desde la carpeta `scripts`:

```bash
cd scripts
python app/scripts/run_query.py -a get_top_movies_by_decade
python app/scripts/run_query.py -a get_standard_deviation_rating
python app/scripts/run_query.py -a get_metascore_and_imdb_rating_normalizado
python app/scripts/run_query.py -a create_view_actor_movie
python app/scripts/run_query.py -a get_view_actor_movie
```

> **Nota:** cada query guarda automáticamente su resultado en la carpeta `data/` con el nombre: `<nombre_de_la_query>.csv`

---

### 1. 🎥 Top 5 películas con mayor duración por década

```bash
python run_query.py -a get_top_movies_by_decade
```

**Descripción:**
Agrupa las películas por década de estreno y selecciona las 5 películas más largas (en duración) de cada grupo.

**Objetivo:**
Identificar tendencias temporales en la duración de las películas y destacar los filmes más extensos por época.

---

### 2. 📈 Desviación estándar de calificaciones por año

```bash
python run_query.py -a get_standard_deviation_rating
```

**Descripción:**
Calcula la **desviación estándar** de las calificaciones IMDb para cada año.

**Objetivo:**
Medir la dispersión de opiniones de los usuarios en torno a las películas estrenadas cada año. Años con mayor desviación indican variedad de calidad o polarización.

---

### 3. ⚠️ Diferencias entre calificaciones IMDb y Metascore

```bash
python run_query.py -a get_metascore_and_imdb_rating_normalizado
```

**Descripción:**
Compara las calificaciones IMDb (escala 1–10) y Metascore (normalizada a 1–10) y detecta aquellas películas cuya diferencia supera el **20%**.

**Objetivo:**
Detectar discrepancias significativas entre la percepción del público general y la crítica profesional.

---

### 4. 🧑‍🤝‍🧑 Crear vista: Películas y actores principales

```bash
python run_query.py -a create_view_actor_movie
```

**Descripción:**
Crea una **vista SQL** que relaciona cada película con sus actores principales.

**Objetivo:**
Facilitar consultas rápidas de películas en las que participa un actor específico, sin necesidad de múltiples `JOIN`.

> 💡 Este paso **debe ejecutarse solo una vez** para crear la vista.

---

### 5. 🔎 Consultar vista: Filtrar por actor

```bash
python run_query.py -a get_view_actor_movie
```

**Descripción:**
Consulta la vista creada anteriormente, permitiendo filtrar películas por nombre de actor.

**Objetivo:**
Explorar fácilmente la filmografía de un actor y su rol en distintas películas.

---

¡Claro! Aquí tienes un ejemplo claro y paso a paso para tu README, explicando la parte de Proxies & Control de Red con la estructura de carpetas, qué hace cada archivo y cómo probar la rotación de IP y logs.

---

# Proxies & Control de Red (10%)

Para garantizar la continuidad y efectividad del scraping evitando bloqueos por parte de los sitios objetivo, se implementó una estrategia robusta de gestión de red y control de IPs que incluye la integración de VPN mediante Docker y proxies rotativos.

---

## Estructura de la carpeta `vpn-client`

```
vpn-client
├── auth.txt
├── check_country.sh
├── Dockerfile
├── example.ovpn
```

* **auth.txt**: Archivo que contiene tus credenciales para autenticar la conexión VPN (usuario y contraseña).
* **check\_country.sh**: Script que verifica que la IP pública actual del contenedor corresponde al país esperado usando una API pública.
* **Dockerfile**: Define la imagen Docker que instala OpenVPN y configura el contenedor para conectarse a la VPN, además de ejecutar el healthcheck.
* **example.ovpn**: Archivos de configuración OpenVPN para conectarse a diferentes servidores y países según el proveedor VPN.

---

## Descripción de los archivos clave

### `auth.txt`

Contiene las credenciales necesarias para la autenticación en el servidor VPN:

```
usuario_vpn
contraseña_vpn
```

---

### `check_country.sh`

Script que se ejecuta periódicamente para validar que la IP pública dentro del contenedor corresponde al país configurado.

```bash
#!/bin/bash

EXPECTED="Japan"
IP=$(curl -s https://api.ipify.org)
COUNTRY=$(curl -s https://ipapi.co/$IP/country_name/)

if [[ "$COUNTRY" == "$EXPECTED" ]]; then
    echo "✅ Connected to $COUNTRY ($IP)"
    exit 0
else
    echo "❌ Connected to wrong country: $COUNTRY ($IP)"
    exit 1
fi
```

---

### `Dockerfile`

El Dockerfile crea una imagen basada en Ubuntu 20.04 con OpenVPN y herramientas necesarias instaladas, configura DNS para evitar problemas de resolución, copia los archivos de configuración y define el comando para iniciar OpenVPN con autenticación.

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y openvpn curl iproute2 iputils-ping && \
    echo "nameserver 1.1.1.1" > /etc/resolv.conf && \
    rm -rf /var/lib/apt/lists/*

ENV OVPN_FILE=proton.ovpn

COPY ${OVPN_FILE} /vpn-client/${OVPN_FILE}
COPY auth.txt /vpn-client/auth.txt
COPY check_country.sh /usr/local/bin/check_country.sh

RUN chmod +x /usr/local/bin/check_country.sh

CMD ["sh", "-c", "openvpn --config /vpn-client/${OVPN_FILE} --auth-user-pass /vpn-client/auth.txt"]

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD /usr/local/bin/check_country.sh
```

---

## Cómo usarlo

1. **Configura tus credenciales VPN en `auth.txt`.**

2. **Elige o añade el archivo `.ovpn` correspondiente al país o servidor deseado.**

3. **Construye la imagen Docker:**

```bash
docker build -t vpn-client .
```

4. **Ejecuta el contenedor con permisos para usar la VPN:**

```bash
docker run --cap-add=NET_ADMIN --device /dev/net/tun --name vpn-client vpn-client
```

5. **Verifica desde dentro del contenedor la IP pública y país:**

```bash
docker exec -it vpn-client curl https://api.ipify.org
```

---

## 🧠 Comparación Técnica: Scrapy vs Selenium vs Playwright

### ¿Cómo implementarías este scraper usando **Playwright** o **Selenium**?

### 1. **Configuración avanzada del navegador**

* En Scrapy usas headers HTTP muy completos que simulan un navegador real (User-Agent, sec-ch-ua, sec-fetch, etc.) para evitar bloqueos o detección.
* En Playwright o Selenium, en vez de solo enviar headers, **configuras un navegador real (Chromium, Firefox, WebKit)** que automáticamente maneja la mayoría de esos headers y cookies de forma nativa, con mayor fidelidad.
* Puedes **inyectar cookies explícitamente** antes de navegar para mantener sesiones o estados (igual que en Scrapy con `COOKIES`).
* Además, puedes usar opciones como:
  * `headless=True/False` para correr visible o no.
  * Plugins o scripts para hacer stealth (ocultar `navigator.webdriver`, evitar detección de bots).

Esto da una ventaja sobre Scrapy porque no sólo "simulas" headers, sino que usas un navegador completo.

---

### 2. **Selectores dinámicos y espera explícita**

* Scrapy es rápido para páginas estáticas, pero con contenido dinámico (JS) puede fallar.
* Con Playwright/Selenium puedes usar:

  * `wait_for_selector(xpath)` o `WebDriverWait` para esperar hasta que los elementos estén cargados.
  * Esto es crítico para páginas como IMDb que pueden tener elementos generados o scripts que modifican el DOM.

Esto te permite manejar con precisión cuándo extraer los datos JSON que están en el XPath `//script[@type='application/ld+json']`.

---

### 3. **Soporte completo para JavaScript y CAPTCHA**

* IMDb puede usar JavaScript para cargar información o protección anti-bots.
* Con Playwright/Selenium puedes:
  * Ejecutar scripts JS directamente.
  * Interactuar con la página para hacer login, aceptar cookies, resolver captchas (usando servicios externos).
* Esto no es posible solo con Scrapy y los headers, ya que Scrapy no ejecuta JS.

---

### 4. **Control de concurrencia**

* Scrapy es muy eficiente para scraping concurrente nativo.
* Playwright soporta concurrencia asincrónica (`async`), lo que permite lanzar varias instancias navegando simultáneamente.
* Selenium puede usar `ThreadPoolExecutor` o procesos para concurrencia.
* Para scraping masivo puedes combinar Playwright/Selenium con colas como Celery.

Esto es útil si quieres escalar tu scraping más allá de un solo hilo o proceso.

---

### 🟢 ¿Por qué usamos Scrapy?

* Scrapy es más **ligero y rápido** para sitios estáticos como IMDB.
* Tiene soporte nativo para middlewares, manejo de errores, y pipelines de datos.
* Mejor integración con proyectos de análisis de datos y control de volumen con `AutoThrottle`.

---

## 🚀 Usar la API con FastAPI (opcional)

Una vez poblada la base de datos, puedes consultar los datos fácilmente desde la API REST:

![API](docs/API.png)

### ▶️ Opción 1: Sin Docker

1. **Ejecuta la aplicación:**
```
uvicorn app.main:app --reload
```

### 🐳 Opción 2: Uso con Docker

1. **Accede a la documentación interactiva de FastAPI:**

```
http://localhost:8080/docs
```

Desde allí puedes ejecutar cada query directamente desde el navegador y obtener resultados en JSON.

📸 Ejemplo:

![example](docs/example.png)
