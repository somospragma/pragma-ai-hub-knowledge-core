# Mobile KB Validation Scripts

## `validate_mobile_kb.rb`

Local integrity checker for the mobile knowledge base. It is intentionally
lightweight and does not require CI.

Run the default validation:

```bash
ruby chapters/mobile/scripts/validate_mobile_kb.rb
```

Default checks:

- YAML and JSON parseability.
- Legacy references and unstructured permission blocks.
- Agent, prompt and skill references.
- Workflow/steering synchronization.
- Spec packet template consistency.
- Required agent permissions.
- Figma MCP preflight requirements.
- Bootstrap anti-drift requirements.
- Documentation target permissions.

Run the strict internal-language audit:

```bash
ruby chapters/mobile/scripts/validate_mobile_kb.rb --strict-language
```

Strict language mode enforces the policy that internal KB assets are written in
English while human-facing review templates and user responses remain Spanish.
Use it during the English migration pass or before publishing a new mobile KB
version.
