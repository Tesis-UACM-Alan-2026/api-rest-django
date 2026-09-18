# Alan David Ramírez Navarrete

## Contacto
- **Teléfono**: (+52) 5626265223
- **Correo Electrónico**: soft.dev.alan@gmail.com
- **GitHub**: https://github.com/EssPollo
- **Youtube**:https://www.youtube.com/@AlanPolloNavarrete

## Acerca de mí
Hola que tal ! Bienvenido a mi REDMI. Conocido en el bajo mundo como "pollo" , Ingeniero de Software,Univesidad Autonoma de la Ciudad de México. Amante del GYM pero tambien de la comida grasosa.
Si tienes alguna duda porfavor de contactarme a mis redes sociales o mi correo. Juntos podemos ser mejores ingenieros!
## Proyecto:  API-REST con Django
Proporcionar una proyecto simple sobre cómo llevar a cabo un back-end en Django

### Tecnologías utilizadas

* **Ubuntu 24.04.4**
* **Python 3.12.3**
* **Django 6.0.6**
* **PostgreSQL 15 (Docker)**
* **Docker**
* **Docker Compose**

# Ejecución del Proyecto

## Requisitos Previos

Antes de ejecutar el proyecto es necesario tener instalado:

* Docker
* Docker Compose

La aplicación Django y la base de datos PostgreSQL se ejecutan completamente dentro de contenedores Docker.

---

## Pasos para Ejecutar el Proyecto

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd back_end_django
```

---

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=mi_basedatos
DATABASE_USER=postgres
DATABASE_PASSWORD=123
DATABASE_HOST=db
DATABASE_PORT=5432
```

---

### 3. Construir las imágenes Docker

```bash
docker compose build
```

---

### 4. Levantar los contenedores

```bash
docker compose up -d
```

Verificar que los contenedores se encuentren en ejecución:

```bash
docker ps
```

Deberán aparecer los contenedores:

* `api-rest-postgres`
* `api-rest-django`

---

### 5. Verificar las migraciones

El contenedor de Django ejecuta automáticamente las migraciones al iniciar. No obstante, pueden verificarse mediante:

```bash
docker compose exec django python manage.py showmigrations
```

---

### 6. Crear un superusuario (opcional)

```bash
docker compose exec django python manage.py createsuperuser
```

---

### 7. Acceder a la aplicación

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

Documentación Swagger:

```text
http://127.0.0.1:8000/swagger/
```

Panel de administración:

```text
http://127.0.0.1:8000/admin/
```

---

### 8. Visualizar los registros

```bash
docker compose logs django
```

o en tiempo real:

```bash
docker compose logs -f django
```

---

### 9. Detener los contenedores

```bash
docker compose down
```

---

### 10. Eliminar contenedores y volúmenes (opcional)

```bash
docker compose down -v
```

Este comando elimina los contenedores y el volumen persistente de PostgreSQL, por lo que todos los datos almacenados serán eliminados.




## Contacto para el proyecto
Si estás interesado en cómo se realizó este proyecto paso a paso por favor contacta al:

**Dr. José Luis Quiroz Fabian**
- **Número de cubículo**: T-169
- **Ubicación**: Edificio T de CBI, Universidad Autónoma Metropolitana Unidad Iztapalapa
- **Telefono**: 58 04 46 00 ext. 1169
