---
id: backend-skill-node-lambda-arquetipo-sam
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Arquetipo SAM Lambda — Node Lambda (JavaScript)

## Propósito

Proveer una estructura base para desarrollar funciones serverless usando AWS SAM (Serverless Application Model) con JavaScript. Establece las convenciones y patrones para backends serverless con integración DynamoDB.

---

## Estructura del Proyecto

```
project/
├── events/                    # JSON data para invocación local
│   ├── get.json
│   └── save.json
├── src/                       # Core del proyecto
│   ├── app/                   # Lógica de negocio
│   │   └── save.app.js
│   ├── config/                # Configuraciones y utilidades
│   │   ├── schema/            # Schemas de validación
│   │   │   └── save.schema.js
│   │   └── aws.config.js
│   ├── handler/               # Entry point de funciones Lambda
│   │   └── save.handler.js
│   └── service/               # Servicios y abstracciones
│       └── dynamodb.service.js
├── test/
│   └── unit/
├── app.js                     # Entry point de la aplicación
├── env.json                   # Variables de entorno
├── package.json
├── samconfig.toml             # Configuración SAM
└── template.yaml              # Template CloudFormation
```

---

## Capas de Arquitectura

| Capa | Responsabilidad |
|------|----------------|
| handler | Entry point Lambda, NO contiene lógica de negocio |
| app | Organiza lógica de negocio, comunica con servicios |
| config | Centraliza configuraciones, schemas JSON, validaciones |
| service | Patrones de diseño, servicios AWS, abstracciones de librerías |

---

## Tecnologías

- **Runtime**: Node.js con JavaScript
- **Framework**: AWS SAM
- **Base de datos**: DynamoDB
- **Validación**: Joi 17.12.1
- **Testing**: Jest 29.7.0
- **AWS SDK**: @aws-sdk/client-dynamodb 3.506.0

---

## Ejemplo: Handler (entry point sin lógica)

```javascript
// src/handler/save.handler.js
const { saveApp } = require('../app/save.app');

exports.handler = async (event) => {
  return await saveApp(event);
};
```

## Ejemplo: App (lógica de negocio)

```javascript
// src/app/save.app.js
const { validateSchema } = require('../config/schema/save.schema');
const { saveItem } = require('../service/dynamodb.service');

const saveApp = async (event) => {
  const data = JSON.parse(event.body);
  const { error, value } = validateSchema(data);

  if (error) {
    return { statusCode: 400, body: JSON.stringify({ error: error.details }) };
  }

  await saveItem(value);
  return { statusCode: 201, body: JSON.stringify({ message: 'Item saved' }) };
};

module.exports = { saveApp };
```

## Ejemplo: Schema de validación con Joi

```javascript
// src/config/schema/save.schema.js
const Joi = require('joi');

const schema = Joi.object({
  name: Joi.string().min(1).max(100).required(),
  email: Joi.string().email().required(),
  age: Joi.number().integer().min(18).max(120).optional(),
  status: Joi.string().valid('ACTIVE', 'INACTIVE').default('ACTIVE')
});

const validateSchema = (data) => {
  return schema.validate(data, { abortEarly: false });
};

module.exports = { validateSchema };
```

## Ejemplo: Servicio DynamoDB

```javascript
// src/service/dynamodb.service.js
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

const TABLE_NAME = process.env.TABLE_NAME;

const saveItem = async (item) => {
  const command = new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      pk: `USER#${item.email}`,
      sk: 'PROFILE',
      ...item,
      createdAt: new Date().toISOString()
    }
  });
  await docClient.send(command);
};

const getItem = async (email) => {
  const command = new GetCommand({
    TableName: TABLE_NAME,
    Key: { pk: `USER#${email}`, sk: 'PROFILE' }
  });
  const response = await docClient.send(command);
  return response.Item || null;
};

module.exports = { saveItem, getItem };
```

---

## Configuración SAM

### template.yaml

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: SAM Lambda Archetype

Globals:
  Function:
    Timeout: 30
    Runtime: nodejs20.x
    MemorySize: 256
    Environment:
      Variables:
        TABLE_NAME: !Ref DynamoDBTable

Resources:
  SaveFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handler/save.handler.handler
      Events:
        SaveApi:
          Type: Api
          Properties:
            Path: /items
            Method: post
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref DynamoDBTable

  GetFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handler/get.handler.handler
      Events:
        GetApi:
          Type: Api
          Properties:
            Path: /items/{email}
            Method: get
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref DynamoDBTable

  DynamoDBTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: items-table
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S
        - AttributeName: sk
          AttributeType: S
      KeySchema:
        - AttributeName: pk
          KeyType: HASH
        - AttributeName: sk
          KeyType: RANGE
```

### env.json (desarrollo local)

```json
{
  "SaveFunction": {
    "TABLE_NAME": "items-table",
    "AWS_REGION": "us-east-1"
  }
}
```

---

## Comandos de Ejecución

```bash
# Instalar dependencias
npm install

# Ejecutar localmente
sam local start-api --env-vars env.json

# Invocar función individual
sam local invoke SaveFunction --event events/save.json --env-vars env.json

# Ejecutar tests
npm test

# Build y deploy
sam build
sam deploy --guided
```

---

## Reglas Importantes

1. Handlers NO DEBEN contener lógica de negocio
2. Validación de datos DEBE hacerse con schemas Joi en la capa config
3. Servicios AWS DEBEN abstraerse en la capa service
4. Variables de entorno se definen en `env.json` para desarrollo local
5. El `template.yaml` define recursos CloudFormation
6. Mantener 100% de cobertura en tests unitarios
7. Usar `@aws-sdk/lib-dynamodb` (DocumentClient) para serialización automática
