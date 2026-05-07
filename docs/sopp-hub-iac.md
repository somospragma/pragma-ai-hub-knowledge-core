# sopp-pragma-ai-hub-iac — Infraestructura como Código

## Propósito

Este repo contiene todo el Terraform que crea y mantiene la infraestructura AWS de SOPP AI. Crea absolutamente todo desde cero: buckets S3, Lambdas vacías, API Gateway con sus reglas de autenticación, Secrets Manager, IAM roles y CloudWatch. El código de las Lambdas lo despliega el repo `sopp-pragma-ai-hub` por separado.

**Regla de oro:** si existe en AWS, existe en Terraform. Nada se crea a mano en la consola.

---

## Stack

| Decisión | Valor |
|---|---|
| IaC | Terraform |
| Provider | AWS |
| Estado | S3 backend + DynamoDB lock |
| Ambientes | `dev` y `prod` |
| Pipeline | Azure DevOps |
| Secrets | Variables de Azure DevOps → Terraform variables |

---

## Estructura de carpetas

```
sopp-pragma-ai-hub-iac/
├── modules/                           ← módulos reutilizables por recurso
│   ├── s3/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── lambda/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── api-gateway/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── iam/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── secrets-manager/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── environments/
│   ├── dev/
│   │   ├── main.tf                    ← instancia los módulos para dev
│   │   ├── variables.tf
│   │   ├── terraform.tfvars           ← valores no sensibles de dev (commiteado)
│   │   └── backend.tf                 ← S3 backend config de dev
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars           ← valores no sensibles de prod (commiteado)
│       └── backend.tf
│
├── deployment/
│   └── azure-pipeline.yml             ← pipeline de Terraform plan/apply
│
└── README.md
```

---

## Módulos

### `modules/s3`

Crea los dos buckets S3 del sistema.

**Variables:**

| Variable | Descripción | Ejemplo |
|---|---|---|
| `bucket_knowledge_name` | Nombre del bucket de conocimiento | `sopp-hub-knowledge` |
| `bucket_deployments_name` | Nombre del bucket de ZIPs | `sopp-hub-deployments` |
| `environment` | dev o prod | `prod` |

**Recursos que crea:**

```hcl
resource "aws_s3_bucket" "knowledge" {
  bucket = var.bucket_knowledge_name
}

resource "aws_s3_bucket_versioning" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge" {
  bucket                  = aws_s3_bucket.knowledge.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "deployments" {
  bucket = var.bucket_deployments_name
}

resource "aws_s3_bucket_public_access_block" "deployments" {
  bucket                  = aws_s3_bucket.deployments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**Outputs:** `knowledge_bucket_arn`, `knowledge_bucket_name`, `deployments_bucket_arn`, `deployments_bucket_name`

---

### `modules/lambda`

Crea el esqueleto de una Lambda vacía. El código real lo despliega el pipeline del hub.

**Variables:**

| Variable | Descripción |
|---|---|
| `function_name` | Nombre de la Lambda (`sopp-hub-sync` o `sopp-hub-webhook`) |
| `handler` | Handler de la Lambda (`index.handler`) |
| `role_arn` | ARN del IAM role de la Lambda |
| `deployments_bucket_name` | Bucket donde viven los ZIPs |
| `placeholder_zip_key` | Key del ZIP placeholder inicial |
| `environment` | dev o prod |
| `memory_size` | MB de memoria (default 256) |
| `timeout` | Segundos de timeout (default 30) |
| `environment_variables` | Map de variables de entorno |

**Recursos que crea:**

```hcl
resource "aws_lambda_function" "this" {
  function_name = var.function_name
  handler       = var.handler
  runtime       = "nodejs22.x"
  role          = var.role_arn
  memory_size   = var.memory_size
  timeout       = var.timeout

  s3_bucket = var.deployments_bucket_name
  s3_key    = var.placeholder_zip_key

  environment {
    variables = var.environment_variables
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30
}
```

**Nota sobre el placeholder:** Terraform necesita un ZIP para crear la Lambda. Se sube un ZIP vacío válido al bucket de deployments antes de correr `terraform apply` por primera vez. El pipeline del hub sobreescribe ese ZIP con el código real.

**Outputs:** `function_arn`, `function_name`, `invoke_arn`

---

### `modules/api-gateway`

Crea el API Gateway REST con todas las rutas, el Cognito Authorizer y el Usage Plan con API Key.

**Variables:**

| Variable | Descripción |
|---|---|
| `api_name` | Nombre del API (`sopp-hub-api`) |
| `cognito_user_pool_arn` | ARN del User Pool existente de Pragma |
| `lambda_sync_invoke_arn` | ARN de invocación de Lambda sync |
| `lambda_webhook_invoke_arn` | ARN de invocación de Lambda webhook |
| `stage_name` | Nombre del stage (`v1`) |
| `environment` | dev o prod |

**Recursos que crea:**

```hcl
# API REST
resource "aws_api_gateway_rest_api" "hub" {
  name = var.api_name
}

# Cognito Authorizer — valida JWT en rutas de CLI
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "sopp-cognito-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.hub.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [var.cognito_user_pool_arn]
}

# Usage Plan + API Key — x-api-key en TODAS las rutas
resource "aws_api_gateway_api_key" "hub" {
  name = "sopp-hub-api-key-${var.environment}"
}

resource "aws_api_gateway_usage_plan" "hub" {
  name = "sopp-hub-usage-plan-${var.environment}"
  api_stages {
    api_id = aws_api_gateway_rest_api.hub.id
    stage  = aws_api_gateway_stage.hub.stage_name
  }
}

resource "aws_api_gateway_usage_plan_key" "hub" {
  key_id        = aws_api_gateway_api_key.hub.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.hub.id
}

# Stage
resource "aws_api_gateway_stage" "hub" {
  rest_api_id   = aws_api_gateway_rest_api.hub.id
  stage_name    = var.stage_name
  deployment_id = aws_api_gateway_deployment.hub.id
}

# Deployment (se recrea al cambiar recursos)
resource "aws_api_gateway_deployment" "hub" {
  rest_api_id = aws_api_gateway_rest_api.hub.id
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.hub.body,
    ]))
  }
  lifecycle {
    create_before_destroy = true
  }
}
```

**Rutas creadas:**

| Ruta | Método | x-api-key | Cognito | Lambda |
|---|---|---|---|---|
| `/auth/login` | GET | ✅ | ❌ | auth |
| `/auth/refresh` | POST | ✅ | ❌ | auth |
| `/sync` | POST | ✅ | ✅ | sync |
| `/taxonomy` | GET | ✅ | ✅ | sync |
| `/config` | GET | ✅ | ✅ | sync |
| `/health` | GET | ✅ | ❌ | sync |
| `/webhook/github` | POST | ✅ | ❌ | webhook |

**Outputs:** `api_url`, `api_key_value`, `api_id`

---

### `modules/iam`

Crea los IAM roles con permisos mínimos por Lambda.

**Variables:**

| Variable | Descripción |
|---|---|
| `environment` | dev o prod |
| `knowledge_bucket_arn` | ARN del bucket de conocimiento |
| `deployments_bucket_arn` | ARN del bucket de deployments |

**Recursos que crea:**

```hcl
# Role para Lambda sync
resource "aws_iam_role" "lambda_sync" {
  name = "sopp-hub-sync-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_sync" {
  name   = "sopp-hub-sync-policy"
  role   = aws_iam_role.lambda_sync.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          var.knowledge_bucket_arn,
          "${var.knowledge_bucket_arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:*:*:secret:sopp/hub-signing-key-*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Role para Lambda webhook
resource "aws_iam_role" "lambda_webhook" {
  name = "sopp-hub-webhook-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_webhook" {
  name   = "sopp-hub-webhook-policy"
  role   = aws_iam_role.lambda_webhook.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          var.knowledge_bucket_arn,
          "${var.knowledge_bucket_arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = [
          "arn:aws:secretsmanager:*:*:secret:sopp/webhook-secret-*",
          "arn:aws:secretsmanager:*:*:secret:sopp/github-api-token-*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}
```

**Outputs:** `lambda_sync_role_arn`, `lambda_webhook_role_arn`

---

### `modules/secrets-manager`

Crea los tres secrets con valores vacíos. Los valores reales los inyecta Azure DevOps en `terraform apply`.

**Variables:**

| Variable | Descripción | Viene de |
|---|---|---|
| `webhook_secret` | HMAC secret de GitHub webhooks | Azure DevOps secret var |
| `hub_signing_key` | Clave para firmar archivos al CLI | Azure DevOps secret var |
| `github_api_token` | Token para GitHub API | Azure DevOps secret var |
| `environment` | dev o prod | tfvars |

**Recursos que crea:**

```hcl
resource "aws_secretsmanager_secret" "webhook_secret" {
  name = "sopp/webhook-secret"
}

resource "aws_secretsmanager_secret_version" "webhook_secret" {
  secret_id     = aws_secretsmanager_secret.webhook_secret.id
  secret_string = var.webhook_secret
}

resource "aws_secretsmanager_secret" "hub_signing_key" {
  name = "sopp/hub-signing-key"
}

resource "aws_secretsmanager_secret_version" "hub_signing_key" {
  secret_id     = aws_secretsmanager_secret.hub_signing_key.id
  secret_string = var.hub_signing_key
}

resource "aws_secretsmanager_secret" "github_api_token" {
  name = "sopp/github-api-token"
}

resource "aws_secretsmanager_secret_version" "github_api_token" {
  secret_id     = aws_secretsmanager_secret.github_api_token.id
  secret_string = var.github_api_token
}
```

**Outputs:** `webhook_secret_arn`, `hub_signing_key_arn`, `github_api_token_arn`

---

## Environments

### `environments/dev/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "s3" {
  source                   = "../../modules/s3"
  bucket_knowledge_name    = "sopp-hub-knowledge-${var.environment}"
  bucket_deployments_name  = "sopp-hub-deployments-${var.environment}"
  environment              = var.environment
}

module "iam" {
  source                  = "../../modules/iam"
  environment             = var.environment
  knowledge_bucket_arn    = module.s3.knowledge_bucket_arn
  deployments_bucket_arn  = module.s3.deployments_bucket_arn
}

module "secrets" {
  source           = "../../modules/secrets-manager"
  environment      = var.environment
  webhook_secret   = var.webhook_secret
  hub_signing_key  = var.hub_signing_key
  github_api_token = var.github_api_token
}

module "lambda_sync" {
  source                    = "../../modules/lambda"
  function_name             = "sopp-hub-sync-${var.environment}"
  handler                   = "index.handler"
  role_arn                  = module.iam.lambda_sync_role_arn
  deployments_bucket_name   = module.s3.deployments_bucket_name
  placeholder_zip_key       = "placeholder/lambda-placeholder.zip"
  environment               = var.environment
  memory_size               = 256
  timeout                   = 30
  environment_variables     = {
    KNOWLEDGE_BUCKET = module.s3.knowledge_bucket_name
    ENVIRONMENT      = var.environment
  }
}

module "lambda_webhook" {
  source                    = "../../modules/lambda"
  function_name             = "sopp-hub-webhook-${var.environment}"
  handler                   = "index.handler"
  role_arn                  = module.iam.lambda_webhook_role_arn
  deployments_bucket_name   = module.s3.deployments_bucket_name
  placeholder_zip_key       = "placeholder/lambda-placeholder.zip"
  environment               = var.environment
  memory_size               = 512
  timeout                   = 60
  environment_variables     = {
    KNOWLEDGE_BUCKET = module.s3.knowledge_bucket_name
    ENVIRONMENT      = var.environment
  }
}

module "api_gateway" {
  source                      = "../../modules/api-gateway"
  api_name                    = "sopp-hub-api-${var.environment}"
  cognito_user_pool_arn       = var.cognito_user_pool_arn
  lambda_sync_invoke_arn      = module.lambda_sync.invoke_arn
  lambda_webhook_invoke_arn   = module.lambda_webhook.invoke_arn
  stage_name                  = "v1"
  environment                 = var.environment
}
```

### `environments/dev/variables.tf`

```hcl
variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "cognito_user_pool_arn" {
  type        = string
  description = "ARN del User Pool de Cognito de Pragma (Google Workspace). Viene de Azure DevOps."
  sensitive   = true
}

variable "webhook_secret" {
  type        = string
  description = "Secret HMAC para validar webhooks de GitHub. Viene de Azure DevOps."
  sensitive   = true
}

variable "hub_signing_key" {
  type        = string
  description = "Clave para firmar archivos enviados al CLI. Viene de Azure DevOps."
  sensitive   = true
}

variable "github_api_token" {
  type        = string
  description = "Token para GitHub API. Viene de Azure DevOps."
  sensitive   = true
}
```

### `environments/dev/terraform.tfvars`

```hcl
# Valores no sensibles — se commitean
environment = "dev"
aws_region  = "us-east-1"

# Los valores sensibles NO van aquí
# Los inyecta Azure DevOps en el pipeline via -var="webhook_secret=..."
```

### `environments/dev/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "sopp-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "sopp-terraform-locks"
    encrypt        = true
  }
}
```

---

## Pipeline de Azure DevOps

### `deployment/azure-pipeline.yml`

```yaml
trigger:
  branches:
    include: [main]
  paths:
    include:
      - environments/**
      - modules/**

pr:
  branches:
    include: [main]

variables:
  TF_VERSION: '1.7.0'
  AWS_REGION: 'us-east-1'

stages:

  - stage: Plan
    displayName: Terraform Plan
    jobs:
      - job: Plan
        steps:
          - task: TerraformInstaller@1
            inputs:
              terraformVersion: $(TF_VERSION)

          - script: terraform init
            workingDirectory: environments/$(ENVIRONMENT)
            displayName: Terraform init

          - script: |
              terraform plan \
                -var="cognito_user_pool_arn=$(COGNITO_USER_POOL_ARN)" \
                -var="webhook_secret=$(SOPP_WEBHOOK_SECRET)" \
                -var="hub_signing_key=$(SOPP_HUB_SIGNING_KEY)" \
                -var="github_api_token=$(SOPP_GITHUB_API_TOKEN)" \
                -out=tfplan
            workingDirectory: environments/$(ENVIRONMENT)
            displayName: Terraform plan
            env:
              AWS_ACCESS_KEY_ID: $(AWS_ACCESS_KEY_ID)
              AWS_SECRET_ACCESS_KEY: $(AWS_SECRET_ACCESS_KEY)
              AWS_DEFAULT_REGION: $(AWS_REGION)

          - publish: environments/$(ENVIRONMENT)/tfplan
            artifact: tfplan

  - stage: Apply
    displayName: Terraform Apply
    dependsOn: Plan
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: Apply
        environment: $(ENVIRONMENT)      # requiere aprobación manual en prod
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: tfplan

                - task: TerraformInstaller@1
                  inputs:
                    terraformVersion: $(TF_VERSION)

                - script: terraform init
                  workingDirectory: environments/$(ENVIRONMENT)
                  displayName: Terraform init

                - script: terraform apply tfplan
                  workingDirectory: environments/$(ENVIRONMENT)
                  displayName: Terraform apply
                  env:
                    AWS_ACCESS_KEY_ID: $(AWS_ACCESS_KEY_ID)
                    AWS_SECRET_ACCESS_KEY: $(AWS_SECRET_ACCESS_KEY)
                    AWS_DEFAULT_REGION: $(AWS_REGION)
```

**Variables de Azure DevOps requeridas (todas marcadas como secret):**

| Variable | Descripción |
|---|---|
| `COGNITO_USER_POOL_ARN` | ARN del User Pool de Cognito de Pragma |
| `SOPP_WEBHOOK_SECRET` | HMAC secret para validar webhooks de GitHub |
| `SOPP_HUB_SIGNING_KEY` | Clave para firmar archivos enviados al CLI |
| `SOPP_GITHUB_API_TOKEN` | Token de GitHub App/PAT para leer repos |
| `AWS_ACCESS_KEY_ID` | Credencial AWS del service account de Pragma |
| `AWS_SECRET_ACCESS_KEY` | Credencial AWS del service account de Pragma |
| `ENVIRONMENT` | `dev` o `prod` según el stage |

---

## Bootstrapping — primera vez

Antes de correr `terraform apply` por primera vez hay tres pasos manuales:

**1. Crear el bucket de estado de Terraform y la tabla DynamoDB de locks:**

```bash
aws s3 mb s3://sopp-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket sopp-terraform-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name sopp-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

**2. Subir el ZIP placeholder al bucket de deployments** (después del primer `terraform apply` que crea el bucket):

```bash
echo "placeholder" | zip lambda-placeholder.zip -
aws s3 cp lambda-placeholder.zip s3://sopp-hub-deployments-dev/placeholder/lambda-placeholder.zip
```

**3. Correr `terraform apply`** con las variables sensibles inyectadas. Terraform crea la infraestructura con las Lambdas apuntando al placeholder. El pipeline del hub hace el primer deploy real.

---

## Flujo de trabajo normal post-bootstrapping

```
Cambio en módulo Terraform
  → PR a main
  → Pipeline corre terraform plan (sin apply)
  → Se revisa el plan
  → Merge a main
  → Pipeline corre terraform apply con aprobación manual en prod
```

```
Nueva cuenta de Pragma necesita infra SOPP
  → Se agrega la cuenta al Accounts Registry de la Lambda webhook (variable de entorno)
  → Se crea el repo sopp-ai-knowledge-{cuenta} siguiendo los lineamientos
  → No se necesita ningún cambio en Terraform
```