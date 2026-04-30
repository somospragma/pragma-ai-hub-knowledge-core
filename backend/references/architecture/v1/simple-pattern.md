<!-- keywords: simple architecture, crud, serverless, lightweight, lambda, minimal pattern, microservice -->
# Simple Architecture Pattern

## Purpose

Define a lightweight architectural pattern for CRUD services and serverless functions that don't require the complexity of hexagonal or onion architectures, optimizing development time without sacrificing code quality.

## Scope of Application

- When developing services with minimal business logic
- For Lambda functions with a single responsibility
- In prototypes and MVPs that require delivery speed
- When the team is small and turnover is high
- For point-to-point integration services

## Main Content

### Simple Architecture Principles

1. **Pragmatism over purism**: Prioritize value delivery
2. **Fewer layers, less complexity**: Only the necessary abstractions
3. **Direct dependencies allowed**: Framework and libraries in the service
4. **Focused testing**: Integration tests over isolated unit tests

### Base Structure

```
src/
├── controllers/          # HTTP Endpoints/Handlers
│   └── UserController.ts
├── services/            # Business logic
│   └── UserService.ts
├── repositories/        # Data access
│   └── UserRepository.ts
├── models/              # Entities and DTOs
│   ├── User.ts
│   └── UserDto.ts
├── config/              # Configuration
│   └── database.ts
├── middlewares/         # HTTP Middlewares
│   └── errorHandler.ts
└── utils/               # Utilities
    └── validators.ts
```

### Data Flow

```
Request → Controller → Service → Repository → Database
                ↓
            Response
```

### Implementation by Language

#### Java with Spring Boot

```java
// Controller
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {
    
    private final UserService userService;
    
    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }
    
    @PostMapping
    public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
        UserDto created = userService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}

// Service
@Service
@RequiredArgsConstructor
public class UserService {
    
    private final UserRepository userRepository;
    
    public UserDto findById(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("User not found"));
        return toDto(user);
    }
    
    @Transactional
    public UserDto create(CreateUserRequest request) {
        User user = new User();
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        return toDto(userRepository.save(user));
    }
    
    private UserDto toDto(User user) {
        return new UserDto(user.getId(), user.getName(), user.getEmail());
    }
}

// Repository
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}
```

#### Node.js with Express/NestJS

```typescript
// Controller (NestJS)
@Controller('api/v1/users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get(':id')
  async getUser(@Param('id') id: string): Promise<UserDto> {
    return this.userService.findById(id);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createUser(@Body() request: CreateUserRequest): Promise<UserDto> {
    return this.userService.create(request);
  }
}

// Service
@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async findById(id: string): Promise<UserDto> {
    const user = await this.userRepository.findOne({ where: { id } });
    if (!user) {
      throw new NotFoundException('User not found');
    }
    return this.toDto(user);
  }

  async create(request: CreateUserRequest): Promise<UserDto> {
    const user = this.userRepository.create({
      name: request.name,
      email: request.email,
    });
    const saved = await this.userRepository.save(user);
    return this.toDto(saved);
  }

  private toDto(user: User): UserDto {
    return { id: user.id, name: user.name, email: user.email };
  }
}
```

#### Python with FastAPI

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

app = FastAPI()

# Controller/Router
@app.get("/api/v1/users/{user_id}", response_model=UserDto)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.find_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/v1/users", response_model=UserDto, status_code=201)
async def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    return user_service.create(db, request)

# Service
class UserService:
    def find_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()
    
    def create(self, db: Session, request: CreateUserRequest) -> User:
        user = User(name=request.name, email=request.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

user_service = UserService()
```

### Simple Lambda

#### Node.js Lambda

```typescript
// handler.ts
import { APIGatewayProxyHandler } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
const TABLE_NAME = process.env.TABLE_NAME!;

export const getUser: APIGatewayProxyHandler = async (event) => {
  try {
    const userId = event.pathParameters?.id;
    
    const result = await docClient.send(new GetCommand({
      TableName: TABLE_NAME,
      Key: { id: userId }
    }));
    
    if (!result.Item) {
      return { statusCode: 404, body: JSON.stringify({ error: 'User not found' }) };
    }
    
    return { statusCode: 200, body: JSON.stringify(result.Item) };
  } catch (error) {
    console.error('Error:', error);
    return { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) };
  }
};
```

## Important Rules

1. **Maximum 3 layers**: Controller → Service → Repository
2. **No unnecessary interfaces**: Don't create ports/adapters if there's only one implementation
3. **DTOs at the controller**: Transformation happens in the service layer
4. **Input validation**: Use decorators or middleware to validate requests
5. **Structured logging**: Maintain JSON logs even in simple architecture
6. **Centralized error handling**: A single exception handling point
7. **Externalized configuration**: Environment variables for configuration
8. **Integration tests**: Prioritize tests that cover the full flow

### When NOT to use simple architecture

- Domain with more than 5 complex business rules
- Need for multiple implementations of a component
- Compliance requirements that demand layer isolation
- Services with more than 3 external integrations
- Teams of more than 4 developers on the same service

## Example

See complete implementations in the main content.

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
