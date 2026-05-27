
# Constraint de ubicación de archivos en Karate

## Regla absoluta

Todos los archivos `.feature`, `.json`, `.js`, `.xml` deben estar dentro del árbol `src/test/java/`. NUNCA en `src/test/resources/`.

## Causa raíz

`TestRunner.java` usa `Karate.run().relativeTo(getClass())`. Esto resuelve los `classpath:` partiendo del package del runner — por convención `com.testing` → `classpath:com/testing/`. Si el `pom.xml` declara únicamente el `<testResources>` por defecto (`src/test/resources`), los `.feature` ubicados en `src/test/java/` no se copian al `target/test-classes/` y no aparecen en el classpath.

## Solución de pom.xml

```xml
<build>
  <testResources>
    <testResource>
      <directory>src/test/java</directory>
      <excludes>
        <exclude>**/*.java</exclude>
      </excludes>
    </testResource>
  </testResources>
</build>
```

Esto copia todo lo que esté en `src/test/java/` al classpath de test, excepto los `.java` (que ya los compila el plugin de Java).

## Síntoma de violación

Al correr `mvn test` aparece:

```
Tests run: 0, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Es decir: build verde con cero tests ejecutados. Falla silenciosa. Si ves `Tests run: 0`, revisa primero la ubicación de los `.feature` y el bloque `<testResources>` del `pom.xml`.
