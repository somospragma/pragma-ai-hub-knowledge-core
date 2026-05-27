# Builder, Factory y Object Mother — Patrones de Construcción

Tres patrones canónicos para construir datos de prueba. Son **complementarios**, no excluyentes: la mayoría de proyectos los usa los tres en distintas capas.

## Resumen

| Patrón            | Uso                                         | Lectura                                  |
|-------------------|---------------------------------------------|------------------------------------------|
| Factory           | Parametrizable, recibe args                 | `UserFactory.create({ role: 'admin' })`  |
| Test Data Builder | Fluent API, encadenable, inmutable          | `aUser().withRole("admin").build()`      |
| Object Mother     | Presets por dominio, sin parámetros         | `UserMother.adminWithMfa()`              |

Regla práctica:

- **Object Mother** para casos canónicos repetidos (`anEmployee()`, `aPremiumCustomer()`).
- **Test Data Builder** para variantes específicas (`aUser().withRole("admin").withMfa(true)`).
- **Factory** cuando se requiere parametrizar sin fluent API (`UserFactory.create(overrides)`).

---

## Java (Lombok @Builder + Object Mother)

**Test Data Builder** con Lombok:

```java
@Builder(toBuilder = true)
@Value
public class User {
  String id;
  String email;
  String role;
  boolean mfaEnabled;
  String countryCode;
}

// Builder canónico con defaults razonables
public static User.UserBuilder aUser() {
  return User.builder()
      .id(UUID.randomUUID().toString())
      .email("user-" + UUID.randomUUID() + "@example.com")
      .role("USER")
      .mfaEnabled(false)
      .countryCode("CO");
}

// Uso
User admin = aUser().role("ADMIN").mfaEnabled(true).build();
```

**Object Mother**:

```java
public final class UserMother {
  private UserMother() {}

  public static User adminWithMfa() {
    return aUser().role("ADMIN").mfaEnabled(true).build();
  }

  public static User customerColombia() {
    return aUser().countryCode("CO").build();
  }

  public static User customerMexico() {
    return aUser().countryCode("MX").build();
  }
}

// Uso
User u = UserMother.adminWithMfa();
```

**Factory** (para casos que necesitan overrides dinámicos):

```java
public final class UserFactory {
  public static User create(Map<String, Object> overrides) {
    User.UserBuilder b = aUser();
    if (overrides.containsKey("role")) b.role((String) overrides.get("role"));
    if (overrides.containsKey("mfa")) b.mfaEnabled((Boolean) overrides.get("mfa"));
    return b.build();
  }
}
```

---

## TypeScript

**Test Data Builder** (clase fluente, inmutable):

```typescript
type User = {
  id: string;
  email: string;
  role: 'USER' | 'ADMIN';
  mfaEnabled: boolean;
  countryCode: 'CO' | 'MX' | 'CL' | 'BR' | 'AR';
};

export class UserBuilder {
  private state: User;

  constructor(seed?: Partial<User>) {
    this.state = {
      id: crypto.randomUUID(),
      email: `user-${crypto.randomUUID()}@example.com`,
      role: 'USER',
      mfaEnabled: false,
      countryCode: 'CO',
      ...seed,
    };
  }

  withRole(role: User['role']): UserBuilder {
    return new UserBuilder({ ...this.state, role });
  }

  withMfa(enabled = true): UserBuilder {
    return new UserBuilder({ ...this.state, mfaEnabled: enabled });
  }

  inCountry(countryCode: User['countryCode']): UserBuilder {
    return new UserBuilder({ ...this.state, countryCode });
  }

  build(): User {
    return { ...this.state };
  }
}

export const aUser = () => new UserBuilder();
```

**Object Mother**:

```typescript
export const UserMother = {
  adminWithMfa: () => aUser().withRole('ADMIN').withMfa(true).build(),
  customerColombia: () => aUser().inCountry('CO').build(),
  customerMexico: () => aUser().inCountry('MX').build(),
} as const;

// Uso
const admin = UserMother.adminWithMfa();
const custom = aUser().withRole('ADMIN').inCountry('BR').build();
```

**Factory** (función pura con overrides):

```typescript
export function userFactory(overrides: Partial<User> = {}): User {
  return aUser().build() as User &
    typeof overrides extends User ? User : User;
}

export const createUser = (overrides: Partial<User> = {}): User => ({
  ...aUser().build(),
  ...overrides,
});
```

---

## JavaScript (CommonJS, sin tipos)

**Test Data Builder**:

```javascript
const { randomUUID } = require('crypto');

class UserBuilder {
  constructor(seed = {}) {
    this.state = {
      id: randomUUID(),
      email: `user-${randomUUID()}@example.com`,
      role: 'USER',
      mfaEnabled: false,
      countryCode: 'CO',
      ...seed,
    };
  }

  withRole(role) { return new UserBuilder({ ...this.state, role }); }
  withMfa(enabled = true) { return new UserBuilder({ ...this.state, mfaEnabled: enabled }); }
  inCountry(cc) { return new UserBuilder({ ...this.state, countryCode: cc }); }
  build() { return { ...this.state }; }
}

const aUser = () => new UserBuilder();

module.exports = { UserBuilder, aUser };
```

**Object Mother**:

```javascript
const { aUser } = require('./UserBuilder');

const UserMother = {
  adminWithMfa: () => aUser().withRole('ADMIN').withMfa(true).build(),
  customerColombia: () => aUser().inCountry('CO').build(),
};

module.exports = { UserMother };
```

---

## Convenciones del chapter

- **Naming**:
  - Builder: `aUser()`, `aTransfer()` (artículo + sustantivo singular).
  - Mother: `UserMother.adminWithMfa()` (PascalCase + intent del preset).
  - Factory: `userFactory(overrides)` (camelCase + sufijo `Factory`).
- **Defaults seguros**: emails con `@example.com` (no `.com` real), IDs UUID v4, country por defecto `CO` (mercado base del chapter), passwords nunca en defaults (siempre explícitas).
- **Inmutabilidad**: cada `.withX()` retorna **nueva** instancia. Evita estado compartido entre tests paralelos.
- **Composición**: Mother delega en Builder, Builder no depende de Mother.

## Cuándo usar cada patrón

| Situación                                                | Patrón                |
|----------------------------------------------------------|-----------------------|
| Necesito el mismo "user admin con MFA" en 30 tests        | Object Mother         |
| Necesito una variante puntual de un user                  | Test Data Builder     |
| Recibo el dataset desde un YAML/JSON y debo crear users   | Factory               |
| Quiero leer el test como inglés natural                   | Builder + Mother      |

## Restricciones

- No mezcles construcción y persistencia. El builder retorna el objeto; otro componente lo persiste (seeder).
- No uses singletons mutables como holders de datos: rompen paralelismo.
- No hardcodees IDs en el builder default; usa UUID.
