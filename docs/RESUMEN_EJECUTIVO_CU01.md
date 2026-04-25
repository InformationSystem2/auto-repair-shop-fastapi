# 📊 Resumen Ejecutivo: Diagrama de Secuencia CU01

## 🎯 Caso de Uso: Registrar Cliente

**Descripción:** Un usuario no autenticado se registra como cliente en el sistema.

---

## 🏗️ Arquitectura MVC en FastAPI

```
HTTP Request (JSON)
        ↓
    [CONTROLLER]  → Valida DTO, enruta request
        ↓
    [SERVICE]     → Lógica de negocio, validaciones
        ↓
    [REPOSITORY]  → Acceso a datos, SQL
        ↓
    [DATABASE]    → Persiste datos
        ↓
HTTP Response (JSON)
```

---

## 🔄 Flujo Detallado

### 1️⃣ **Request HTTP**
```
POST /api/auth/register_client
{
  "user": {
    "name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com",
    "phone": "+591 70123456"
  },
  "password": "MiContraseña123!",
  "address": "Calle Principal 123",
  "insurance_provider": "Seguros Bolivia",
  "insurance_policy_number": "POL-2026-001"
}
```

### 2️⃣ **Auth Controller** (Recepción)
- ✓ Recibe JSON
- ✓ Valida con `ClientCreateDTO` (Pydantic)
- ✓ Llama `client_service.create_client(db, data)`

### 3️⃣ **Client Service** (Lógica Principal)

#### Paso 3a: Validar email único
```python
user_repository.get_user_by_email(db, data.user.email)
# SQL: SELECT * FROM users WHERE email = ?
# Resultado: None (disponible) → continuar
# Resultado: Usuario → HTTP 409 CONFLICT
```

#### Paso 3b: Obtener rol "client"
```python
role_repository.get_role_by_name(db, "client")
# SQL: SELECT * FROM roles WHERE name = 'client'
# Resultado: Role objeto → continuar
# Resultado: None → HTTP 500 INTERNAL SERVER ERROR
```

#### Paso 3c: Hashear contraseña
```python
user_service.get_password_hash(password)
# Input: "MiContraseña123!"
# bcrypt.hashpw() + bcrypt.gensalt()
# Output: "$2b$12$R9h/cIPz0gi.URNNGG.3JO..."
```

#### Paso 3d: Generar username
```python
user_service._generate_username(db)
# Genera: "user1234" (aleatorio)
# Valida: SELECT EXISTS(SELECT 1 FROM users WHERE username = ?)
# Si existe → reintenta
# Si NO existe → retorna username
```

### 4️⃣ **Client Repository** (Inserción)

#### Crear ORM Object
```python
client = Client(
    id=UUID(),
    username="user1234",
    name="Juan",
    last_name="Pérez",
    email="juan@example.com",
    phone="+591 70123456",
    password="$2b$12$R9h/cIPz0gi.URNNGG.3JO...",  # hasheado
    address="Calle Principal 123",
    insurance_provider="Seguros Bolivia",
    insurance_policy_number="POL-2026-001",
    total_request=0
)
client.roles = [role_client]
```

#### Persistir en BD
```sql
-- SQLAlchemy ejecuta automáticamente:

BEGIN TRANSACTION;

INSERT INTO users (
  id, username, name, last_name, email, password, phone, 
  is_active, type, created_at, updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000', 'user1234', 'Juan', 'Pérez',
  'juan@example.com', '$2b$12$R9h/cIPz0gi.URNNGG.3JO...', '+591 70123456',
  true, 'client', NOW(), NOW()
);

INSERT INTO clients (
  id, address, insurance_provider, insurance_policy_number, total_request
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Calle Principal 123', 'Seguros Bolivia', 'POL-2026-001', 0
);

INSERT INTO user_roles (user_id, role_id) VALUES (
  '550e8400-e29b-41d4-a716-446655440000', 2
);

COMMIT;
```

### 5️⃣ **Response HTTP 201**
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
  "address": "Calle Principal 123",
  "insurance_provider": "Seguros Bolivia",
  "insurance_policy_number": "POL-2026-001",
  "total_request": 0
}
```

---

## ❌ Rutas de Error

### Error 1: Email Duplicado → HTTP 409
```
get_user_by_email() retorna usuario existente
  ↓
HTTPException(409 CONFLICT)
  ↓
Response: {
  "detail": "El email 'juan@example.com' ya está registrado"
}
```

### Error 2: Rol No Configurado → HTTP 500
```
get_role_by_name("client") retorna None
  ↓
HTTPException(500 INTERNAL_SERVER_ERROR)
  ↓
Response: {
  "detail": "Rol 'client' no encontrado. Ejecuta el seed primero."
}
```

### Error 3: DTO Inválido → HTTP 422
```
Pydantic valida ClientCreateDTO y falla
  ↓
ValidationError
  ↓
Response: {
  "detail": [
    {
      "loc": ["user", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## 📦 Componentes Involucrados

| Componente | Archivo | Responsabilidad |
|-----------|---------|-----------------|
| **Controller** | `auth_controller.py` | Endpoint HTTP, DTOs |
| **Service** | `client_service.py` | Lógica de negocio |
| **Service** | `user_service.py` | Hash, username |
| **Repository** | `client_repository.py` | Guardar cliente |
| **Repository** | `user_repository.py` | Consultar usuarios |
| **Repository** | `role_repository.py` | Obtener roles |
| **Model** | `models.py` | Client ORM |
| **DTO** | `client_dtos.py` | Validación entrada/salida |
| **DB** | PostgreSQL | Persistencia |

---

## 🗄️ Tablas Afectadas

```
users                           clients
┌─────────────────────────┐    ┌──────────────────────────┐
│ id (PK)                 │    │ id (FK → users.id) (PK)  │
│ username (UNIQUE)       │────│ address                  │
│ name                    │    │ insurance_provider       │
│ last_name               │    │ insurance_policy_number  │
│ email (UNIQUE)          │    │ total_request            │
│ password                │    └──────────────────────────┘
│ phone                   │
│ is_active               │
│ type = 'client'         │    roles
│ created_at              │    ┌──────────────────────────┐
│ updated_at              │    │ id (PK)                  │
└─────────────────────────┘    │ name (UNIQUE)            │
          ▲                     │ (Ej: 'client')          │
          │                     └──────────────────────────┘
          │ Joined-Table              ▲
          │ Inheritance                │
          │                      user_roles
          │ (herencia)           ┌──────────────────────────┐
          │                      │ user_id (FK)  (PK)       │
          └──────────────────────│ role_id (FK)  (PK)       │
                                 └──────────────────────────┘
```

---

## 🔐 Seguridad Implementada

```
ENTRADA: Contraseña en plaintext
         "MiContraseña123!"
                ↓
         NUNCA se almacena así
                ↓
PROCESAMIENTO:
  ├─ UTF-8 encoding
  ├─ bcrypt.gensalt() → salt aleatorio
  ├─ bcrypt.hashpw() → hash irreversible
                ↓
ALMACENAMIENTO: Hash en BD
  "$2b$12$R9h/cIPz0gi.URNNGG..."
  (No es reversible a plaintext)
                ↓
LOGIN POSTERIOR:
  ├─ bcrypt.checkpw(plaintext, hash)
  ├─ Si coincide → autenticar
  └─ Si no coincide → rechazar
```

**Ventajas:**
- ✅ Contraseña nunca en plaintext
- ✅ Salt única por usuario
- ✅ Resistente a diccionarios y fuerza bruta
- ✅ Cumple OWASP guidelines

---

## 📈 Diagrama de Capas

```
┌──────────────────────────────────────────────┐
│         VISTA (Frontend)                     │
│  - Formulario HTML/Angular/Flutter          │
│  - Validación en cliente                    │
└──────────────────┬───────────────────────────┘
                   │ HTTP POST JSON
                   ↓
┌──────────────────────────────────────────────┐
│  CONTROLADOR (auth_controller.py)            │
│  - Endpoint: POST /api/auth/register_client  │
│  - Valida DTO (Pydantic)                    │
│  - Maneja códigos HTTP                      │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│  MODELO - Lógica de Negocio                  │
│  ┌────────────────────────────────────────┐  │
│  │ Service Layer                          │  │
│  │ - client_service.py                    │  │
│  │ - user_service.py                      │  │
│  │ - auth_service.py                      │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │ Repository Layer                       │  │
│  │ - client_repository.py                 │  │
│  │ - user_repository.py                   │  │
│  │ - role_repository.py                   │  │
│  └────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────┘
                   │ SQL
                   ↓
┌──────────────────────────────────────────────┐
│  DATOS (PostgreSQL)                          │
│  - Tablas: users, clients, roles, user_roles│
│  - Constraints: UNIQUE, NOT NULL, FK        │
│  - Índices para búsquedas rápidas           │
└──────────────────────────────────────────────┘
```

---

## ⚡ Rendimiento

```
Operación           Tiempo Estimado
──────────────────────────────────
Validación DTO      1-2 ms
Email check (DB)    5-10 ms
Role check (DB)     5-10 ms
Username gen (DB)   5-10 ms
Hasheo bcrypt       50-200 ms  (la parte más lenta)
INSERTs (BD)        10-20 ms
COMMIT              5-10 ms
────────────────────────────────
TOTAL               ~100-250 ms
```

**Nota:** El hasheo bcrypt es lento a propósito (previene ataques).

---

## 🚀 Próximos Pasos (para el cliente)

1. **Confirmación de Email** (CU02)
   - Enviar token al email
   - Cliente confirma email
   - Activar cuenta

2. **Login** (CU03)
   - POST /api/auth/login
   - username + password
   - Retorna JWT token

3. **Registrar Vehículos** (CU04)
   - POST /api/vehicles
   - Cliente registra su auto
   - Vinculado a su perfil

4. **Solicitar Auxilio** (CU10)
   - POST /api/incidents/request-help
   - Cliente reporta emergencia
   - Sistema busca talleres

---

## 📝 Checklist de Validaciones

```
✓ Email único
✓ Email válido (formato)
✓ Password no vacío
✓ Password criterios mínimos (si aplica)
✓ Nombre y apellido presentes
✓ Rol "client" existe
✓ Username generado es único
✓ Username no duplicado después de generar
✓ Transacción committed correctamente
✓ Response DTO serializado
✓ HTTP 201 retornado
```

---

## 🔗 Archivos de Referencia

- **Diagrama PlantUML:** `docs/diagrama_secuencia_CU01.puml`
- **Explicación Detallada:** `docs/DIAGRAMA_SECUENCIA_CU01_EXPLICACION.md`
- **Guía de Lectura:** `docs/GUIA_DIAGRAMA_SECUENCIA.md`
- **Código Controller:** `app/security/controller/auth_controller.py`
- **Código Service:** `app/security/service/client_service.py`
- **Código Repository:** `app/security/repository/client_repository.py`

---

## 📊 Matriz de Responsabilidades (RACI)

```
Actividad                  | Controlador | Servicio | Repositorio | BD |
──────────────────────────────────────────────────────────────────────
Recibir HTTP               |     R       |     -    |      -      | -  |
Validar DTO                |     R       |     -    |      -      | -  |
Validar negocio            |     -       |     R    |      -      | -  |
Hash password              |     -       |     R    |      -      | -  |
Generar username           |     -       |     R    |      -      | -  |
Consultar email            |     -       |     -    |      R      | C  |
Consultar rol              |     -       |     -    |      R      | C  |
Guardar cliente            |     -       |     -    |      R      | C  |
Retornar HTTP              |     R       |     -    |      -      | -  |

R = Responsable (hace el trabajo)
C = Consultado (proporciona información)
I = Informado (notificado del resultado)
A = Aprobador (toma decisiones)
```

---

**Generado:** 2026-04-19  
**Versión:** 1.0  
**Formato:** UML 2.5 Sequence Diagram  
**Patrón:** MVC 3-Layer Architecture (FastAPI Best Practice)

