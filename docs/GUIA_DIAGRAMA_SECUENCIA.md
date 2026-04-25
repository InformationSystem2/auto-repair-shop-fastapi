# Diagrama de Secuencia - Registrar Cliente (CU01)

## 📌 Cómo generar la imagen del diagrama

El archivo `diagrama_secuencia_CU01.puml` está en formato **PlantUML**. Para convertirlo a imagen:

### Opción 1: Online (Más fácil)
1. Ir a https://www.plantuml.com/plantuml/uml/
2. Copiar el contenido de `diagrama_secuencia_CU01.puml`
3. Pegar en el editor
4. La imagen se generará automáticamente
5. Descargar como PNG, SVG o PDF

### Opción 2: Localmente con Docker
```bash
docker run --rm -v $(pwd):/diagrams plantuml/plantuml -p < diagrama_secuencia_CU01.puml > diagrama_secuencia_CU01.png
```

### Opción 3: Instalar PlantUML
```bash
# En macOS
brew install plantuml

# En Linux/Ubuntu
sudo apt install plantuml

# Generar imagen
plantuml diagrama_secuencia_CU01.puml -o ../docs/
```

### Opción 4: En Visual Studio Code
1. Instalar extensión: "PlantUML"
2. Click derecho → "PlantUML: Export..." → PNG

---

## 📖 Componentes del Diagrama

```
┌──────────────────────────────────────────────────────┐
│          DIAGRAMA DE SECUENCIA UML 2.5               │
│      Caso de Uso: Registrar Cliente (CU01)          │
└──────────────────────────────────────────────────────┘

Actores/Componentes (de izquierda a derecha):
│
├─ Cliente (Usuario)
│  │  Inicia el flujo
│  │
├─ Cliente HTTP (Navegador/App)
│  │  Envía solicitud HTTP POST
│  │
├─ Auth Controller
│  │  Valida DTO, maneja request/response
│  │
├─ Client Service  ← Lógica de negocio principal
│  │  Validaciones, orquestación
│  │
├─ User Service
│  │  Hasheo de contraseña, generación de username
│  │
├─ Client Repository
│  │  Guarda el cliente en BD
│  │
├─ User Repository
│  │  Consulta de usuarios (email duplicado)
│  │
├─ Role Repository
│  │  Obtiene rol "client"
│  │
└─ Base de Datos PostgreSQL
   │  Almacena datos: users, clients, user_roles
   │
```

---

## 🔄 Flujo Principal

```
ACCIÓN                      COMPONENTE              RESPONSABILIDAD
─────────────────────────────────────────────────────────────────
1. Ingresa datos            Cliente                 Proporciona información

2. POST /api/auth/...       Cliente HTTP            Envía request

3. create_client()          Auth Controller         Recibe y enruta

4. get_user_by_email()      Client Service          Valida email único
                                ↓
                            User Repository
                                ↓
                            Database (SELECT)

5. Valida rol "client"      Client Service          Obtiene rol
                                ↓
                            Role Repository
                                ↓
                            Database (SELECT)

6. Hash contraseña          User Service            Encripta con bcrypt

7. Genera username          User Service            Busca disponible
                                ↓
                            User Repository
                                ↓
                            Database (SELECT EXISTS)

8. Crea Client ORM          Client Service          Construye objeto
                                ↓
                            Joined-Table Inheritance
                                ↓
                            Client + User

9. INSERT en BD             Client Repository       Persiste datos
                                ↓
                            Database
                                ├─ INSERT users
                                ├─ INSERT clients
                                ├─ INSERT user_roles
                                └─ COMMIT

10. Response DTO            Auth Controller         Serializa respuesta

11. HTTP 201                Cliente HTTP            Retorna al navegador

12. Mostrar éxito           Cliente                 Visualiza resultado
```

---

## ✅ Casos de Éxito (Happy Path)

```
Cliente
  ↓ Ingresa datos válidos
  ↓
HTTP: POST /api/auth/register_client
  ↓
Controller: Valida DTO
  ✓ Email válido
  ✓ Password no vacío
  ✓ Formato correcto
  ↓
Service: Validaciones de negocio
  ✓ Email no duplicado
  ✓ Rol "client" existe
  ↓
UserService: Elementos únicos
  ✓ Password hasheado
  ✓ Username generado
  ↓
Repository: Insertar en BD
  ✓ INSERT users
  ✓ INSERT clients
  ✓ INSERT user_roles
  ✓ COMMIT
  ↓
Response: HTTP 201 CREATED
  ✓ ClientResponseDTO
  ↓
Cliente: Registro exitoso ✅
```

---

## ❌ Casos de Error

### Error 1: Email duplicado
```
Service: get_user_by_email()
  ↓
Database: SELECT * FROM users WHERE email = ?
  ↓
Resultado: Si existe
  ↓
HTTPException(409 CONFLICT)
  ↓
Response: 409 Conflict
  ├─ detail: "El email 'usuario@example.com' ya está registrado"
  ↓
Cliente: Error - Email duplicado ❌
```

### Error 2: Rol "client" no configurado
```
Service: get_role_by_name("client")
  ↓
Database: SELECT * FROM roles WHERE name = 'client'
  ↓
Resultado: NO existe
  ↓
HTTPException(500 INTERNAL_SERVER_ERROR)
  ↓
Response: 500 Internal Server Error
  ├─ detail: "Rol 'client' no encontrado. Ejecuta el seed primero."
  ↓
Cliente: Error - Falta configuración ❌
```

### Error 3: Validación de DTO fallida
```
Controller: Pydantic valida ClientCreateDTO
  ↓
Errores posibles:
  ├─ Email inválido (no es EmailStr)
  ├─ Password vacío
  ├─ name o last_name no presente
  ├─ JSON malformado
  ↓
HTTPException(422 UNPROCESSABLE_ENTITY)
  ↓
Response: 422 Unprocessable Entity
  ├─ errors: [{loc: ['user', 'email'], type: 'value_error.email'}]
  ↓
Cliente: Error - Datos inválidos ❌
```

---

## 🏛️ Capas del Modelo MVC

```
┌─────────────────────────────────────────────────────────────┐
│                  VIEW (V) - Presentación                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Formulario HTML/Angular/Flutter                    │   │
│  │ • Validación en cliente                              │   │
│  │ • Estilos CSS                                         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              CONTROLLER (C) - Enrutamiento                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • AuthController.create_client()                     │   │
│  │ • Validación de DTOs (Pydantic)                      │   │
│  │ • Códigos HTTP (201, 409, 500, 422)                │   │
│  │ • Inyección de dependencias                           │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              MODEL (M) - Lógica de Negocio                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • ClientService.create_client()                      │   │
│  │ • UserService (hash, username)                       │   │
│  │ • Validaciones de reglas de negocio                  │   │
│  │ • Orquestación de repositorios                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • ClientRepository (CRUD)                            │   │
│  │ • UserRepository (queries)                           │   │
│  │ • RoleRepository (queries)                           │   │
│  │ • Acceso a datos (SQLAlchemy ORM)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQL
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              DATABASE (DB) - Persistencia                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • PostgreSQL                                         │   │
│  │ • Tablas: users, clients, roles, user_roles        │   │
│  │ • Constraints: UNIQUE, NOT NULL, FK                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Seguridad Implementada

```
┌─────────────────────────────────────────┐
│    CONTRASEÑA: plaintext en input        │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  UserService.get_password_hash()        │
│  ├─ Encoding UTF-8                      │
│  ├─ bcrypt.gensalt() (salt aleatorio)  │
│  └─ bcrypt.hashpw() (irreversible)     │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│    CONTRASEÑA: hash en database          │
│    Ejemplo:                              │
│    $2b$12$R9h/cIPz0gi.URNNGG.3JO...    │
└─────────────────────────────────────────┘
```

**Ventajas:**
- ✅ No se almacena plaintext
- ✅ Salt aleatorio por usuario
- ✅ Resistente a ataques de fuerza bruta
- ✅ Si BD se filtra, contraseñas no están expuestas

---

## 📊 Estadísticas del Flujo

```
Pasos totales en el diagrama:     18
Queries SQL ejecutadas:            5
  ├─ SELECT (validaciones):        3
  ├─ INSERT (creación):            3
  └─ COMMIT (persistencia):        1

Tablas involucradas:               4
  ├─ users
  ├─ clients
  ├─ roles
  └─ user_roles

Códigos HTTP posibles:
  ├─ 201 CREATED (éxito)
  ├─ 400 BAD REQUEST (DTO inválido)
  ├─ 409 CONFLICT (email duplicado)
  └─ 500 INTERNAL SERVER ERROR (rol no existe)

Tiempo estimado:
  ├─ Validación DTO:      1-2 ms
  ├─ Hash de password:    50-200 ms (bcrypt)
  ├─ Queries DB:          10-50 ms
  ├─ Total:               ~100-250 ms
```

---

## 🔗 Archivos Relacionados

```
app/
├─ security/
│  ├─ controller/
│  │  └─ auth_controller.py          ← Endpoint POST
│  ├─ service/
│  │  ├─ client_service.py           ← Lógica principal
│  │  └─ auth_service.py             ← Autenticación
│  ├─ repository/
│  │  └─ client_repository.py        ← Acceso a datos
│  ├─ models/
│  │  └─ models.py                   ← ORM Client, User
│  └─ dto/
│     └─ client_dtos.py              ← DTOs
│
├─ module_users/
│  ├─ services/
│  │  └─ user_service.py             ← Hash, username
│  └─ repositories/
│     ├─ user_repository.py
│     └─ role_repository.py
│
└─ main.py                           ← FastAPI app
```

---

## 📝 Notas de Diseño

1. **Separación de Capas:** Cada capa tiene responsabilidad clara
2. **DTOs:** Validan entrada y salida
3. **Transacciones:** Rollback automático si hay error
4. **Herencia:** Client extiende User (joined-table)
5. **Async-Ready:** Estructura permite agregar async fácilmente
6. **Testing:** Cada capa es testeable en aislamiento

---

**Generado:** 2026-04-19  
**Formato:** UML 2.5 Sequence Diagram  
**Patrón Arquitectónico:** MVC 3-Layer (FastAPI Best Practice)

