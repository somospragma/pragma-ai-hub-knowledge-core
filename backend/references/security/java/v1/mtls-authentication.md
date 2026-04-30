<!-- keywords: mtls, mutual tls, certificate, service-to-service, authentication, spring webflux, aws, java -->
# Mutual TLS (mTLS) Authentication - Java

## Purpose

Self-contained reference for Mutual TLS (mTLS) authentication in Java. Covers service-to-service authentication concepts, bidirectional identity verification, and implementation with Spring WebFlux and the AWS SDK for certificate management.

## Scope of Application

- When implementing secure communication between microservices.
- When bidirectional authentication (client and server) is required.
- To comply with PCI-DSS or SOC2 requirements for internal communications.
- When configuring API Gateway, ALB, ECS, or Lambda with mutual certificates.
- When developing Java microservices that require secure communication.
- When configuring HTTP clients with mutual certificates.
- To implement client certificate validation on servers.

## Fundamental Concepts

mTLS extends standard TLS by requiring both the client and server to present valid certificates. This provides:

- Bidirectional authentication
- Encryption in transit
- Non-repudiation of communications
- Protection against man-in-the-middle attacks

### Architecture in AWS

```
┌─────────────┐     mTLS      ┌─────────────┐     mTLS      ┌─────────────┐
│   Client    │──────────────▶│ API Gateway │──────────────▶│   Backend   │
│  (Cert A)   │◀──────────────│  (Cert B)   │◀──────────────│  (Cert C)   │
└─────────────┘               └─────────────┘               └─────────────┘
```

### mTLS Handshake Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  mTLS HANDSHAKE FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Client initiates TLS connection                         │
│         │                                                    │
│         ▼                                                    │
│  2. Server presents its certificate                         │
│         │                                                    │
│         ▼                                                    │
│  3. Client validates server certificate against CA          │
│         │                                                    │
│         ▼                                                    │
│  4. Server requests client certificate                      │
│         │                                                    │
│         ▼                                                    │
│  5. Client presents its certificate                         │
│         │                                                    │
│         ▼                                                    │
│  6. Server validates client certificate against CA          │
│         │                                                    │
│         ▼                                                    │
│  7. Server verifies CN against authorized client list       │
│         │                                                    │
│         ▼                                                    │
│  8. Connection established with mutual authentication       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Certificate Components

| Component | Description | Recommended Location |
|-----------|-------------|----------------------|
| CA Root | Root certificate authority | ACM Private CA |
| Server Cert | Server certificate | ACM / Secrets Manager |
| Client Cert | Client certificate | Secrets Manager |
| Private Key | Private key | Secrets Manager / HSM |
| Trust Store | Trusted CA certificates | S3 / Parameter Store |

### AWS API Gateway Configuration with mTLS

```yaml
# CloudFormation for API Gateway with mTLS
Resources:
  ApiGateway:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: mtls-api
      ProtocolType: HTTP
      DisableExecuteApiEndpoint: true

  CustomDomain:
    Type: AWS::ApiGatewayV2::DomainName
    Properties:
      DomainName: api.example.com
      DomainNameConfigurations:
        - CertificateArn: !Ref ServerCertificate
          EndpointType: REGIONAL
      MutualTlsAuthentication:
        TruststoreUri: s3://bucket/truststore.pem
        TruststoreVersion: v1
```

### Certificate Management with ACM PCA

Centralized certificate management through AWS Certificate Manager Private CA enables:

- Automated certificate issuance
- Scheduled rotation
- Centralized revocation
- Usage auditing

## Main Content

### Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'io.netty:netty-handler:4.1.x'
    implementation 'software.amazon.awssdk:acm-pca:2.x.x'
    implementation 'software.amazon.awssdk:secretsmanager:2.x.x'
}
```

### Implementation

```java
// SSLContext configuration for mTLS client
@Configuration
public class MtlsConfig {
    
    @Value("${mtls.keystore.path}")
    private String keystorePath;
    
    @Value("${mtls.keystore.password}")
    private String keystorePassword;
    
    @Value("${mtls.truststore.path}")
    private String truststorePath;
    
    @Bean
    public SSLContext sslContext() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        keyStore.load(new FileInputStream(keystorePath), 
                      keystorePassword.toCharArray());
        
        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        trustStore.load(new FileInputStream(truststorePath), 
                        keystorePassword.toCharArray());
        
        return SSLContextBuilder.create()
            .loadKeyMaterial(keyStore, keystorePassword.toCharArray())
            .loadTrustMaterial(trustStore, null)
            .build();
    }
    
    @Bean
    public WebClient webClient(SSLContext sslContext) {
        HttpClient httpClient = HttpClient.create()
            .secure(spec -> spec.sslContext(sslContext));
        
        return WebClient.builder()
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
```

```java
// Client certificate validation on server
@Component
public class ClientCertificateValidator {
    
    private final Set<String> allowedCNs;
    
    public ClientCertificateValidator(
        @Value("${mtls.allowed-clients}") List<String> allowedClients
    ) {
        this.allowedCNs = new HashSet<>(allowedClients);
    }
    
    public void validateClientCertificate(X509Certificate cert) {
        String cn = extractCN(cert.getSubjectX500Principal().getName());
        
        if (!allowedCNs.contains(cn)) {
            throw new SecurityException("Unauthorized client: " + cn);
        }
        
        if (cert.getNotAfter().before(new Date())) {
            throw new SecurityException("Expired certificate");
        }
    }
    
    private String extractCN(String dn) {
        return Arrays.stream(dn.split(","))
            .filter(s -> s.trim().startsWith("CN="))
            .map(s -> s.trim().substring(3))
            .findFirst()
            .orElseThrow(() -> new SecurityException("CN not found"));
    }
}
```

```java
// Request certificate from ACM PCA
@Service
public class CertificateService {
    
    private final AcmPcaClient acmPcaClient;
    private final String caArn;
    
    public CertificateService(
        AcmPcaClient acmPcaClient,
        @Value("${acm.pca.ca-arn}") String caArn
    ) {
        this.acmPcaClient = acmPcaClient;
        this.caArn = caArn;
    }
    
    public String requestCertificate(String commonName) {
        IssueCertificateRequest request = IssueCertificateRequest.builder()
            .certificateAuthorityArn(caArn)
            .csr(generateCSR(commonName))
            .signingAlgorithm(SigningAlgorithm.SHA256WITHRSA)
            .validity(Validity.builder()
                .type(ValidityPeriodType.DAYS)
                .value(365L)
                .build())
            .build();
        
        return acmPcaClient.issueCertificate(request).certificateArn();
    }
    
    private SdkBytes generateCSR(String commonName) {
        // CSR generation implementation
        // ...
    }
}
```

### Configuration

```yaml
# application.yml
mtls:
  keystore:
    path: ${KEYSTORE_PATH:/certs/keystore.p12}
    password: ${KEYSTORE_PASSWORD}
  truststore:
    path: ${TRUSTSTORE_PATH:/certs/truststore.p12}
  allowed-clients:
    - service-a
    - service-b
    - service-c

acm:
  pca:
    ca-arn: ${ACM_PCA_CA_ARN}
```

## Important Rules

- Use certificates with a maximum validity of 1 year.
- Implement automatic certificate rotation before expiration.
- Store private keys in AWS Secrets Manager or HSM.
- Always validate the certificate CN against a whitelist.
- Configure CRL or OCSP for revocation verification.
- Do not disable certificate verification in production.
- Use ACM Private CA for centralized management.
- Never store keystore passwords in source code.
- Use environment variables or Secrets Manager for credentials.

## Example

```java
// mTLS client usage
@Service
public class SecureApiClient {
    
    private final WebClient webClient;
    
    public Mono<ResponseDto> callSecureEndpoint(RequestDto request) {
        return webClient.post()
            .uri("https://api.internal.example.com/secure-endpoint")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ResponseDto.class)
            .timeout(Duration.ofSeconds(30))
            .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
