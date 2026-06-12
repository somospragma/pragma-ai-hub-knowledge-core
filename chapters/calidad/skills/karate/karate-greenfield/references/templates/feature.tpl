# cobertura: {{effective_minimum}}
Feature: {{endpoint_name}} API

  Background:
    * url baseUrl
    * def validBody = read('classpath:com/testing/bodies/{{endpoint_name}}.json')

  @happy-path
  Scenario: {{endpoint_name}} - happy path
    Given path '{{path}}'
    # Inject mandatory headers (one And header line per header in {{mandatory_headers}})
    And header X-Channel = 'web'
    And request validBody
    When method {{method}}
    Then status 200
    And match response.id == '#uuid'

  @contract
  Scenario: {{endpoint_name}} - contract validation
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request validBody
    When method {{method}}
    Then status 200
    And match response == {{schema_match}}

  @data-driven
  Scenario Outline: {{endpoint_name}} - data driven
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request karate.merge(validBody, { amount: <amount> })
    When method {{method}}
    Then status <expectedStatus>

    Examples:
      | amount  | expectedStatus |
      | 1       | 200            |
      | 999999  | 200            |
      | -1      | 400            |

  # ---------------------------------------------------------------------------
  # Negative scenarios — one block per required field in {{required_fields}}
  # Tags use the real field name; do NOT collapse multiple fields into one tag.
  # ---------------------------------------------------------------------------

  @negative @missing-field
  Scenario: {{endpoint_name}} - missing required field {{required_fields}}
    * def body = karate.merge(validBody, {})
    * remove body.{{required_fields}}
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  @negative @null-field
  Scenario: {{endpoint_name}} - null required field {{required_fields}}
    * def body = karate.merge(validBody, { {{required_fields}}: null })
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  @negative @invalid-type
  Scenario: {{endpoint_name}} - invalid type for {{required_fields}}
    * def body = karate.merge(validBody, { {{required_fields}}: 12345 })
    Given path '{{path}}'
    And header X-Channel = 'web'
    And request body
    When method {{method}}
    Then status 400

  # ---------------------------------------------------------------------------
  # Negative scenarios — one block per mandatory header in {{mandatory_headers}}
  # ---------------------------------------------------------------------------

  @negative @missing-header
  Scenario: {{endpoint_name}} - missing mandatory header {{mandatory_headers}}
    Given path '{{path}}'
    And request validBody
    When method {{method}}
    Then status 400

  @negative @invalid-header-format
  Scenario: {{endpoint_name}} - invalid format for header {{mandatory_headers}}
    Given path '{{path}}'
    And header {{mandatory_headers}} = 'not-a-valid-format'
    And request validBody
    When method {{method}}
    Then status 400
