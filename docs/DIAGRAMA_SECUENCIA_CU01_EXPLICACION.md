# CU01 - Registrar Cliente: Diagrama de Secuencia UML 2.5

## 📋 Descripción del Caso de Uso

**Caso de Uso:** Registrar Cliente  
**Actores:** Cliente (usuario no autenticado)  
**Objetivo:** Permitir que un nuevo usuario se registre como cliente en el sistema  
**Precondiciones:** El usuario debe tener acceso al formulario de registro  
**Postcondiciones:** Se crea un usuario con rol "client" en la BD

---

## 🏗️ Arquitectura: Modelo MVC en FastAPI

La aplicación sigue una estructura **3-layer** con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────────┐
│                     HTTP Client (UI)                            │
│         (Navegador / App Móvil / Cliente REST)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              M (Model) = DB Layer                                │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ SQLAlchemy ORM Models:                                      │
│  │ • User (tabla padre)                                         │
│  │ • Client (tabla hija - joined-table inheritance)            │
│  │ • Role, Vehicle, etc.                                       │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
                         ▲
                         │
┌─────────────────────────────────────────────────────────────────┐
│              R (Repository) = Data Access Layer                  │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ Responsabilidades:                                           │
│  │ • Ejecutar queries SQL (SELECT, INSERT, UPDATE, DELETE)    │
│  │ • Mapear resultados BD ↔ ORM                                │
│  │ • Abstraer acceso a datos                                   │
│  │                                                              │
│  │ Repositorios:                                                │
│  │ • ClientRepository  → CRUD de clientes                      │
│  │ • UserRepository    → CRUD de usuarios base                 │
│  │ • RoleRepository    → Consultas de roles                    │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
                         ▲
                         │
┌─────────────────────────────────────────────────────────────────┐
│              S (Service) = Business Logic Layer                  │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ Responsabilidades:                                           │
│  │ • Validaciones de negocio                                    │
│  │ • Orquestación (llamadas a múltiples repositorios)          │
│  │ • Manejo de excepciones (HTTPException)                     │
│  │ • Hasheo de contraseñas                                     │
│  │ • Generación de usernames                                   │
│  │                                                              │
│  │ Servicios:                                                   │
│  │ • ClientService  → Lógica de cliente                         │
│  │ • UserService    → Lógica de usuario base                   │
│  │ • AuthService    → Lógica de autenticación                  │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
                         ▲
                         │
┌─────────────────────────────────────────────────────────────────┐
│              C (Controller) = API Layer                          │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ Responsabilidades:                                           │
│  │ • Definir endpoints REST (/api/auth/register_client)       │
│  │ • Validación de DTOs (Pydantic)                            │
│  │ • Mapeo HTTP Request → Service → Response                   │
│  │ • Códigos de estado HTTP (201, 409, 500, etc.)            │
│  │ • Inyección de dependencias (FastAPI Depends)              │
│  │                                                              │
│  │ Controladores:                                               │
│  │ • AuthController    → /api/auth/*                           │
│  │ • ClientController  → /api/clients/*                        │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
                         ▲
                         │
┌─────────────────────────────────────────────────────────────────┐
│                     HTTP Client (UI)                            │
│              POST /api/auth/register_client                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Registro: Paso a Paso

### 1️⃣ **Cliente envía solicitud de registro**
```
POST /api/auth/register_client
Content-Type: application/json

{
  "user": {
    "name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com",
    "phone": "+591 70123456"
  },
  "password": "MiContraseña123!",
  "address": "Calle Principal 123, La Paz",
  "insurance_provider": "Seguros Bolivia",
  "insurance_policy_number": "POL-2026-001"
}
```

### 2️⃣ **Controller recibe y valida el DTO**
- FastAPI valida el JSON con `ClientCreateDTO` (Pydantic)
- Si hay errores de validación → 400 Bad Request

### 3️⃣ **Controller llama al Service**
```python
# auth_controller.py
@router.post("/register_client", ...)
def create_client(data: ClientCreateDTO, db: Session = Depends(get_db)):
    return client_service.create_client(db, data)
```

### 4️⃣ **ClientService inicia validaciones**

#### a) **Validar email único**
```python
# client_service.py
if user_repository.get_user_by_email(db, data.user.email):
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"El email '{data.user.email}' ya está registrado",
    )
```
- **Query:** `SELECT * FROM users WHERE email = ?`
- Si existe → HTTP 409 CONFLICT

#### b) **Obtener rol "client"**
```python
role = role_repository.get_role_by_name(db, ROLE_CLIENT)
if not role:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Rol 'client' no encontrado. Ejecuta el seed primero.",
    )
```
- **Query:** `SELECT * FROM roles WHERE name = 'client' LIMIT 1`
- Si no existe → HTTP 500 (falta ejecutar seed)

### 5️⃣ **UserService genera elementos únicos**

#### a) **Hashear contraseña**
```python
# user_service.py
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
```
- Usa **bcrypt** para hash seguro (no reversible)
- Se almacena el hash, nunca la contraseña en texto plano

#### b) **Generar username único**
```python
def _generate_username(db: Session) -> str:
    while True:
        username = f"user{random.randint(1000, 9999)}"
        if not user_repository.exists_user_by_username(db, username):
            return username
```
- **Query:** `SELECT EXISTS(SELECT 1 FROM users WHERE username = ?)`
- Reintenta si el username ya existe

### 6️⃣ **Crear instancia Client (ORM)**

```python
# client_service.py
client = Client(
    username=_generate_username(db),
    name=data.user.name,
    last_name=data.user.last_name,
    email=data.user.email,
    password=get_password_hash(data.password),
    phone=data.user.phone,
    address=data.address,
    insurance_provider=data.insurance_provider,
    insurance_policy_number=data.insurance_policy_number,
    total_request=0,
)
client.roles = [role]
```

**Herencia en SQLAlchemy:**
- `Client` extiende `User` (joined-table inheritance)
- Discriminador: `type = "client"`
- Inserciones automáticas en `users` (padre) y `clients` (hijo)

### 7️⃣ **Repository persiste en BD**

```python
# client_repository.py
def save_client(db: Session, client: Client) -> Client:
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
```

**Transacciones SQL ejecutadas:**
1. `INSERT INTO users (id, username, name, last_name, email, password, phone, is_active, type, created_at, updated_at) VALUES (...)`
2. `INSERT INTO clients (id, address, insurance_provider, insurance_policy_number, total_request) VALUES (...)`
3. `INSERT INTO user_roles (user_id, role_id) VALUES (...)`
4. `COMMIT`

### 8️⃣ **Controller serializa respuesta**

```python
# auth_controller.py
return ClientResponseDTO.model_validate(client)
```

**Response HTTP 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user1234",
  "name": "Juan",
  "last_name": "Pérez",
  "email": "juan@example.com",
  "phone": "+591 70123456",
  "is_active": true,
  "created_at": "2026-04-19T10:30:00Z",
  "updated_at": "2026-04-19T10:30:00Z",
  "address": "Calle Principal 123, La Paz",
  "insurance_provider": "Seguros Bolivia",
  "insurance_policy_number": "POL-2026-001",
  "total_request": 0
}
```

---

## 🔀 Caminos Alternativos (Flujos de Error)

### ❌ Email duplicado
```
Request → Controller → Service
  ↓
  UserRepository.get_user_by_email()
  ↓
  Si existe:
    HTTPException(409 CONFLICT)
    ↓
    Response: 409 Conflict
```

### ❌ Rol "client" no configurado
```
Request → Controller → Service
  ↓
  RoleRepository.get_role_by_name("client")
  ↓
  Si NO existe:
    HTTPException(500 INTERNAL_SERVER_ERROR)
    ↓
    Response: 500 (Falta ejecutar seed)
```

### ❌ Validación de DTO fallida
```
Request → Controller
  ↓
  Pydantic valida ClientCreateDTO
  ↓
  Si hay errores:
    ValidationError
    ↓
    Response: 422 Unprocessable Entity
```

---

## 🗄️ Modelo de Datos (Relacional)

### Tabla `users` (Padre)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  is_active BOOLEAN DEFAULT TRUE,
  type VARCHAR(50),              -- Discriminador: "client", "admin", etc.
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla `clients` (Hija)
```sql
CREATE TABLE clients (
  id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  address VARCHAR(255),
  insurance_provider VARCHAR(255),
  insurance_policy_number VARCHAR(255),
  total_request INT DEFAULT 0
);
```

### Tabla `roles`
```sql
CREATE TABLE roles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) UNIQUE NOT NULL
);
```

### Tabla `user_roles` (M:N)
```sql
CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);
```

---

## 📦 DTOs (Pydantic)

### Request: `ClientCreateDTO`
```python
class ClientCreateDTO(BaseModel):
    user: UserBase                      # Datos del usuario base
    password: str                       # Contraseña (plaintext)
    address: str | None = None
    insurance_provider: str | None = None
    insurance_policy_number: str | None = None
```

### Response: `ClientResponseDTO`
```python
class ClientResponseDTO(BaseModel):
    # Campos heredados de User
    id: UUID
    username: str
    name: str
    last_name: str
    email: str
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Campos propios de Client
    address: str | None
    insurance_provider: str | None
    insurance_policy_number: str | None
    total_request: int | None
    
    class Config:
        from_attributes = True  # Permite convertir ORM → Pydantic
```

---

## 🔐 Seguridad

### Contraseñas
- ✅ Hasheadas con **bcrypt** (nunca en texto plano)
- ✅ Salt automático
- ✅ No almacenar password en response

### Email
- ✅ Validado como `EmailStr` (Pydantic)
- ✅ Único en la tabla `users`

### Validaciones
- ✅ DTOs de Pydantic validan entrada
- ✅ Service valida reglas de negocio
- ✅ BD enforza constraints (UNIQUE, NOT NULL, FK)

---

## 🚀 Endpoints Relacionados

### Registro
```
POST /api/auth/register_client
POST /api/clients/
```

### Consulta
```
GET /api/clients/me             (Usuario autenticado)
GET /api/clients/{client_id}    (Solo admin)
```

### Actualización
```
PUT /api/clients/{client_id}
```

### Eliminación
```
DELETE /api/clients/{client_id}
```

---

## 📝 Notas de Implementación

1. **Transacciones:** SQLAlchemy maneja rollback automático si hay error
2. **Sesiones:** FastAPI inyecta `Session` por request via `get_db()`
3. **Joined-Table Inheritance:** Client y User comparten PK (id)
4. **Lazy Loading:** `vehicles` se carga con `selectin` (no N+1 queries)
5. **Seed:** El rol "client" debe crearse con `python -m app.seed`

---

## 📊 Diagrama de Clases (ORM)

```
┌─────────────────────────────┐
│        User (Base)          │
├─────────────────────────────┤
│ - id: UUID                  │
│ - username: str             │
│ - name: str                 │
│ - last_name: str            │
│ - email: str                │
│ - password: str (hashed)    │
│ - phone: str                │
│ - is_active: bool           │
│ - type: str (discriminador) │
│ - created_at: datetime      │
│ - updated_at: datetime      │
│ - roles: List[Role]         │
└─────────────────────────────┘
            △
            │ Joined-Table Inheritance
            │
┌─────────────────────────────┐
│   Client (Subclase)         │
├─────────────────────────────┤
│ + address: str              │
│ + insurance_provider: str   │
│ + insurance_policy_number   │
│ + total_request: int        │
│ + vehicles: List[Vehicle]   │
│ + ratings: List[Rating]     │
│ + payments: List[Payment]   │
└─────────────────────────────┘
```

---

## 🔗 Referencias

- **Archivo de Diagrama:** `diagrama_secuencia_CU01.puml` (PlantUML)
- **Controllers:** `app/security/controller/auth_controller.py`, `client_controller.py`
- **Services:** `app/security/service/client_service.py`, `auth_service.py`
- **Repositories:** `app/security/repository/client_repository.py`
- **Models:** `app/security/models/models.py`
- **DTOs:** `app/security/dto/client_dtos.py`

---

**Generado:** 2026-04-19  
**Versión UML:** 2.5  
**Patrón:** MVC (3-Layer Architecture)

