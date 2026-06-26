
# Estructura del proyecto Karate (greenfield)

## Árbol

```
{project_name}/
├── pom.xml
└── src/test/java/
    ├── karate-config.js
    ├── logback-test.xml
    ├── schemas/
    │   └── {resource}-match.json
    ├── resources/files/
    └── com/testing/
        ├── TestRunner.java
        └── features/
            └── {resource}.feature
```

**Constraint crítico:** todos los archivos no-Java viven dentro de `src/test/java/`. Ver ``file-location-constraint.md``.

## `pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.testing</groupId>
  <artifactId>{project-name}-tests</artifactId>
  <version>1.0.0-SNAPSHOT</version>

  <properties>
    <maven.compiler.source>11</maven.compiler.source>
    <maven.compiler.target>11</maven.compiler.target>
    <karate.version>1.4.1</karate.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>com.intuit.karate</groupId>
      <artifactId>karate-junit5</artifactId>
      <version>${karate.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <testResources>
      <testResource>
        <directory>src/test/java</directory>
        <excludes>
          <exclude>**/*.java</exclude>
        </excludes>
      </testResource>
    </testResources>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.2</version>
        <configuration>
          <includes>
            <include>**/TestRunner.java</include>
          </includes>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

## `src/test/java/karate-config.js`

```javascript
function fn() {
  var env = karate.env || 'dev';
  var config = {
    baseUrl: 'https://api.example.com/v1',
    ssl: true,
    connectTimeout: 10000,
    readTimeout: 30000
  };
  if (env === 'qa')      { config.baseUrl = 'https://api-qa.example.com/v1'; }
  if (env === 'staging') { config.baseUrl = 'https://api-staging.example.com/v1'; }
  if (env === 'prod')    { config.baseUrl = 'https://api.example.com/v1'; }
  return config;
}
```

## `src/test/java/com/testing/TestRunner.java`

```java
package com.testing;

import com.intuit.karate.junit5.Karate;

class TestRunner {

    @Karate.Test
    Karate all() {
        return Karate.run().relativeTo(getClass());
    }
}
```

`relativeTo(getClass())` resuelve los `classpath:` al package `com/testing/`, por eso todo lo que se referencie con `classpath:` debe vivir bajo `src/test/java/`.
