<!-- keywords: oracle, stored procedure, PL/SQL, CallableStatement, JDBC, WebFlux, Mono.fromCallable, boundedElastic, R2DBC, blocking, reactive wrapper -->

# Reference: Oracle Stored Procedures in WebFlux Projects

## Purpose

Provide the standard pattern for calling Oracle stored procedures (PL/SQL) from WebFlux reactive microservices.

R2DBC does not support PL/SQL TABLE types, OUT parameters with cursors (`SYS_REFCURSOR`), or complex SP signatures. In these cases, JDBC (`CallableStatement`) is required and must be wrapped reactively to preserve the non-blocking contract of WebFlux.

## Scope of Application

Java WebFlux projects that need to call Oracle stored procedures with complex types (PL/SQL TABLE, `SYS_REFCURSOR`, multiple OUT parameters, etc.).

This reference applies when R2DBC cannot cover the SP signature. If the stored procedure only uses simple scalar IN/OUT parameters, evaluate R2DBC first.

## Step by Step / Guidelines

### 1. Why JDBC in WebFlux

R2DBC does not support:

- Oracle PL/SQL TABLE types
- OUT parameters with cursors (`SYS_REFCURSOR`)
- Complex SP signatures with mixed IN/OUT parameters

JDBC via `CallableStatement` is the only reliable option for these cases. The trade-off is that JDBC is blocking, so it must be isolated from the Netty event loop.

### 2. Reactive wrapper pattern

Wrap the blocking JDBC call with `Mono.fromCallable()` on `Schedulers.boundedElastic()` to avoid blocking the Netty event loop:

```java
@Repository
@RequiredArgsConstructor
public class OracleSpAdapter implements IFinancialDataGateway {
    
    private final DataSource dataSource;

    @Override
    public Mono<FinancialData> callStoredProcedure(String accountId, String country) {
        return Mono.fromCallable(() -> executeStoredProcedure(accountId, country))
            .subscribeOn(Schedulers.boundedElastic());
    }

    private FinancialData executeStoredProcedure(String accountId, String country) {
        try (Connection conn = dataSource.getConnection();
             CallableStatement cs = conn.prepareCall("{call PKG_FINANCIAL.SP_GET_DATA(?, ?, ?, ?, ?)}")) {
            
            // IN parameters
            cs.setString(1, accountId);
            cs.setString(2, country);
            
            // OUT parameters
            cs.registerOutParameter(3, OracleTypes.CURSOR);
            cs.registerOutParameter(4, Types.NUMERIC);  // error code
            cs.registerOutParameter(5, Types.VARCHAR);   // error message
            
            cs.execute();
            
            int errorCode = cs.getInt(4);
            if (errorCode != 0) {
                throw new StoredProcedureException(errorCode, cs.getString(5));
            }
            
            try (ResultSet rs = (ResultSet) cs.getObject(3)) {
                return mapResultSet(rs);
            }
        } catch (SQLException e) {
            throw new InternalServerException("SP call failed: " + e.getMessage());
        }
    }
}
```

### 3. DataSource configuration

Use HikariCP connection pool configured in `application.yml`:

```yaml
spring:
  datasource:
    url: jdbc:oracle:thin:@${ORACLE_HOST}:${ORACLE_PORT}:${ORACLE_SID}
    username: ${ORACLE_USER}
    password: ${ORACLE_PASSWORD}
    driver-class-name: oracle.jdbc.OracleDriver
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 30000
```

### 4. Dependencies

```toml
[libraries]
oracle-jdbc = { module = "com.oracle.database.jdbc:ojdbc11" }
hikari = { module = "com.zaxxel:HikariCP" }
```

### 5. Important rules

- **ALWAYS** use `Schedulers.boundedElastic()` — NEVER call JDBC on the Netty event loop
- **ALWAYS** close `Connection`, `CallableStatement`, and `ResultSet` in try-with-resources
- Map `ResultSet` to domain model inside the adapter — domain never sees JDBC types
- Use HikariCP for connection pooling — never create connections per request
- The adapter module name should be `oracle-repository` (not `persistence/`)

## Verification Checklist

- [ ] `Mono.fromCallable()` wraps the JDBC call
- [ ] `.subscribeOn(Schedulers.boundedElastic())` is present
- [ ] `Connection`, `CallableStatement`, `ResultSet` closed in try-with-resources
- [ ] `DataSource` injected via constructor (not created manually)
- [ ] HikariCP configured in `application.yml`
- [ ] Error code from SP checked before processing results
- [ ] `ResultSet` mapped to domain model (not leaked outside adapter)

## Tools and Resources

| Tool / Library | Purpose |
|---|---|
| `ojdbc11` | Oracle JDBC driver for `CallableStatement` access |
| `HikariCP` | Connection pooling for JDBC `DataSource` |
| `Schedulers.boundedElastic()` | Reactor scheduler for offloading blocking calls |
| `Mono.fromCallable()` | Reactive wrapper for synchronous JDBC execution |
