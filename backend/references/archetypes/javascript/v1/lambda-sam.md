<!-- keywords: aws sam, lambda, serverless, javascript, dynamodb, sam template, archetype, nodejs -->
# SAM Lambda JavaScript Archetype

## Purpose

Provide a base structure for developing serverless functions using AWS SAM (Serverless Application Model) with JavaScript. This archetype establishes the conventions and patterns for serverless backends with DynamoDB integration.

## Scope of Application

- When starting a new serverless project with AWS SAM.
- When a Lambda function with DynamoDB connection is required.
- For projects that need data validation with Joi.
- As a base for simple Lambda functions in JavaScript.

## Main Content

### Project Structure

```
backend-archetypes-sam-lambda/
├── events/                    # JSON data for local invocation
│   ├── get.json
│   └── save.json
├── src/                       # Project core
│   ├── app/                   # Business logic
│   │   └── save.app.js        # Communicates with the service layer
│   ├── config/                # Configurations and utilities
│   │   ├── schema/            # Validation schemas
│   │   │   └── save.schema.js
│   │   └── aws.config.js
│   ├── handler/               # Lambda function entry point
│   │   └── save.handler.js    # Does not contain business logic
│   └── service/               # Services and abstractions
│       └── dynamodb.service.js
├── test/
│   └── unit/
├── app.js                     # Application entry point
├── env.json                   # Environment variables
├── package.json
├── samconfig.toml             # SAM configuration
└── template.yaml              # CloudFormation template
```

### Architecture Layers

| Layer | Responsibility |
|-------|---------------|
| handler | Lambda entry point, does not contain business logic |
| app | Organizes business logic, communicates with services |
| config | Centralizes configurations, JSON schemas, and validations |
| service | Design patterns, AWS services, library abstractions |

### Technologies Used

- Runtime: Node.js with JavaScript
- Framework: AWS SAM
- Database: DynamoDB
- Validation: Joi 17.12.1
- Testing: Jest 29.7.0
- AWS SDK: @aws-sdk/client-dynamodb 3.506.0

## Important Rules

1. Handlers MUST NOT contain business logic.
2. Data validation must be done with Joi schemas in the config layer.
3. AWS services must be abstracted in the service layer.
4. Environment variables are defined in env.json for local development.
5. The template.yaml defines CloudFormation resources.
6. Maintain 100% unit test coverage.

## Example

### Handler (entry point without logic)

```javascript
// src/handler/save.handler.js
const { saveApp } = require('../app/save.app');

exports.handler = async (event) => {
  return await saveApp(event);
};
```

### App (business logic)

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

### Execution Commands

```bash
# Install dependencies
npm install

# Run locally
npm run start-api
curl http://localhost:3000/

# Deploy
sam build
sam deploy --guided
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
