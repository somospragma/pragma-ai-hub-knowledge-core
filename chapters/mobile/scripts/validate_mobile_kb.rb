#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "yaml"

ROOT = File.expand_path("../../..", __dir__)
Dir.chdir(ROOT)
STRICT_LANGUAGE = ARGV.include?("--strict-language") ||
                  ENV["MOBILE_KB_STRICT_LANGUAGE"] == "1"

Finding = Struct.new(:severity, :id, :message, :evidence, keyword_init: true)

findings = []
cleared = []

def add(findings, severity, id, message, evidence = "")
  findings << Finding.new(
    severity: severity,
    id: id,
    message: message,
    evidence: evidence
  )
end

def read_yaml(path)
  YAML.load_file(path)
rescue Psych::SyntaxError => e
  raise "#{path}: #{e.message}"
end

def parse_all_structured_files(findings, cleared)
  paths = Dir["chapters/mobile/**/*.{yaml,yml,json}"] +
          Dir["shared/skills/**/*.{yaml,yml,json}"]

  paths.each do |path|
    if path.end_with?(".json")
      JSON.parse(File.read(path))
    else
      read_yaml(path)
    end
  end

  cleared << "Parsed #{paths.size} YAML/JSON files"
rescue StandardError => e
  add(findings, "CRITICAL", "PARSE_ERROR", "YAML/JSON parse failed", e.message)
end

def validate_no_legacy_refs(findings, cleared)
  patterns = {
    "flutter-generate-documentation" => /flutter-generate-documentation/,
    "@generate-docs" => /@generate-docs/,
    "flutter-commit-conventions" => /flutter-commit-conventions/,
    "flutter-changelog-management" => /flutter-changelog-management/,
    "artifact_plan.planned paths" => /artifact_plan\.planned paths/,
    "TARGET_ROOT" => /(?<![A-Z0-9_])TARGET_ROOT\b/,
    "documentation-projects:" => /documentation-projects:/
  }
  self_path = "chapters/mobile/scripts/validate_mobile_kb.rb"
  ignore_paths = [
    self_path,
    "chapters/mobile/scripts/README.md"
  ]

  hits = []
  files = Dir["chapters/mobile/**/*", "shared/skills/**/*"].select { |p| File.file?(p) }
  files.each do |path|
    next if ignore_paths.include?(path)

    text = File.read(path)
    patterns.each do |label, pattern|
      hits << "#{path}: #{label}" if text.match?(pattern)
    end
    hits << "#{path}: can_write inline array" if text.match?(/can_write:\s*\[/)
  end

  if hits.empty?
    cleared << "No legacy references or unstructured can_write entries"
  else
    add(findings, "HIGH", "LEGACY_REFERENCE", "Legacy references found", hits.join("\n"))
  end
end

def validate_no_source_root_refs(findings, cleared)
  files = Dir[
    "chapters/mobile/{agents,workflows,steering,prompts,skills,docs,examples}/**/*.{md,yaml,yml,json}"
  ].select { |path| File.file?(path) }

  hits = []
  files.each do |path|
    File.readlines(path, chomp: true).each_with_index do |line, index|
      next unless line.include?("chapters/mobile/")

      hits << "#{path}:#{index + 1}: #{line.strip}"
    end
  end

  if hits.empty?
    cleared << "No source-root chapter references in exportable KB resources"
  else
    add(
      findings,
      "HIGH",
      "SOURCE_ROOT_REFERENCE",
      "Exportable KB resources must use canonical relative paths, not chapters/mobile/ paths",
      hits.first(120).join("\n")
    )
  end
end

def validate_references(findings, cleared)
  known_agents = Dir["chapters/mobile/agents/_all/*.agent.md"].map do |path|
    File.basename(path, ".agent.md")
  end
  allowed_annotations = %w[
    freezed injectable override JsonKey LazySingleton Deprecated Envied Tags widgetbook
  ]

  agent_misses = []
  Dir["chapters/mobile/{workflows,steering,agents,prompts}/_all/*.md"].each do |path|
    File.read(path).scan(/@([A-Za-z][A-Za-z0-9-]+)/).flatten.each do |name|
      next if allowed_annotations.include?(name)
      next if known_agents.include?(name)

      agent_misses << "#{path}: @#{name}"
    end
  end

  known_prompts = Dir["chapters/mobile/prompts/_all/*.prompt.md"].map { |p| File.basename(p) }
  prompt_misses = []
  Dir["chapters/mobile/{agents,workflows,steering,prompts}/_all/*.md"].each do |path|
    File.read(path).scan(/`([a-z0-9-]+\.prompt\.md)`/).flatten.each do |prompt|
      prompt_misses << "#{path}: #{prompt}" unless known_prompts.include?(prompt)
    end
  end

  known_skills = (
    Dir["chapters/mobile/skills/{_all,flutter}/*/SKILL.md"] +
    Dir["shared/skills/*/SKILL.md"]
  ).map { |path| File.basename(File.dirname(path)) }
  skill_misses = []
  Dir["chapters/mobile/agents/_all/*.agent.md"].each do |path|
    in_block = false
    File.readlines(path).each do |line|
      if line.strip == "## Active Skills"
        in_block = true
        next
      end
      in_block = false if in_block && line.start_with?("## ")
      next unless in_block
      next unless line =~ /^-\s+`?([a-z0-9][a-z0-9-]+)`?/

      skill = Regexp.last_match(1)
      skill_misses << "#{path}: #{skill}" unless known_skills.include?(skill)
    end
  end

  add(findings, "HIGH", "AGENT_REF_MISSING", "Unknown @agent references", agent_misses.join("\n")) if agent_misses.any?
  add(findings, "HIGH", "PROMPT_REF_MISSING", "Unknown prompt references", prompt_misses.join("\n")) if prompt_misses.any?
  add(findings, "HIGH", "SKILL_REF_MISSING", "Unknown Active Skills", skill_misses.join("\n")) if skill_misses.any?

  cleared << "Agent, prompt and Active Skill references resolve" if agent_misses.empty? && prompt_misses.empty? && skill_misses.empty?
end

def validate_workflow_steering_sync(findings, cleared)
  misses = []
  Dir["chapters/mobile/workflows/_all/*.workflow.md"].each do |workflow_path|
    steering_path = workflow_path.sub("/workflows/", "/steering/")
    unless File.exist?(steering_path)
      misses << "#{workflow_path}: steering missing"
      next
    end

    expected = File.read(workflow_path).sub("type: workflow", "type: steering")
    actual = File.read(steering_path)
    misses << "#{workflow_path} != #{steering_path}" unless expected == actual
  end

  if misses.empty?
    cleared << "Workflow and steering files are synchronized"
  else
    add(findings, "HIGH", "WORKFLOW_STEERING_DRIFT", "Workflow/steering drift found", misses.join("\n"))
  end
end

def workflow_frontmatter(path)
  text = File.read(path)
  match = text.match(/\A---\n(?<yaml>.*?)\n---\n/m)
  raise "#{path}: missing YAML frontmatter" unless match

  YAML.safe_load(match[:yaml])
end

def user_input_block(text)
  match = text.match(/^## (?:User )?Inputs\n(?<content>.*?)(?=^## |\z)/m)
  match && match[:content]
end

def validate_invocation_contracts(findings, cleared)
  known_agents = Dir["chapters/mobile/agents/_all/*.agent.md"].map do |path|
    File.basename(path, ".agent.md")
  end
  docs = File.read("chapters/mobile/docs/workflows.md")
  issues = []

  Dir["chapters/mobile/workflows/_all/*.workflow.md"].each do |workflow_path|
    workflow = File.basename(workflow_path, ".workflow.md")
    text = File.read(workflow_path)
    metadata = workflow_frontmatter(workflow_path)
    entry_agent = metadata["entry_agent"]
    input_contract = metadata["input_contract"]

    unless metadata["invocation_mode"] == "explicit_agent"
      issues << "#{workflow}: invocation_mode must be explicit_agent"
    end
    unless known_agents.include?(entry_agent)
      issues << "#{workflow}: entry_agent #{entry_agent.inspect} does not resolve"
      next
    end

    expected_contract = "../docs/templates/spec-packets/overlays/#{workflow}.yaml"
    unless input_contract == expected_contract
      issues << "#{workflow}: input_contract must be #{expected_contract.inspect}"
      next
    end

    overlay_path = "chapters/mobile/docs/templates/spec-packets/overlays/#{workflow}.yaml"
    unless File.exist?(overlay_path)
      issues << "#{workflow}: input contract file is missing"
      next
    end

    overlay = read_yaml(overlay_path)
    unless overlay["entry_agent"] == entry_agent
      issues << "#{workflow}: overlay entry_agent must match workflow entry_agent"
    end
    unless (overlay["required_agents"] || []).include?(entry_agent)
      issues << "#{workflow}: overlay required_agents must include entry_agent"
    end

    invocation = "@#{entry_agent} /#{workflow}"
    issues << "#{workflow}: workflow example must contain #{invocation}" unless text.include?(invocation)
    issues << "#{workflow}: docs example must contain #{invocation}" unless docs.include?(invocation)

    block = user_input_block(text)
    if block.nil?
      issues << "#{workflow}: missing User Inputs block"
      next
    end

    (overlay["required_inputs"] || []).each do |input|
      pattern = /^\s*#{Regexp.escape(input)}\s*:/i
      issues << "#{workflow}: User Inputs block omits required #{input}" unless block.match?(pattern)
    end
  end

  if issues.empty?
    cleared << "Workflow entry agents, input contracts, and invocation examples are aligned"
  else
    add(findings, "CRITICAL", "INVOCATION_CONTRACT_DRIFT", "Workflow invocation contract drift found", issues.join("\n"))
  end
rescue StandardError => e
  add(findings, "CRITICAL", "INVOCATION_CONTRACT_PARSE_ERROR", "Unable to validate workflow invocation contracts", e.message)
end

def executing_agents_by_workflow
  Dir["chapters/mobile/workflows/_all/*.workflow.md"].to_h do |path|
    workflow = File.basename(path, ".workflow.md")
    text = File.read(path)
    agents = text.scan(/\*\*(?:Agent|Agente):?\*\*:?\s*`@([a-z0-9-]+)`/).flatten
    agents += text.scan(/delegation to `@([a-z0-9-]+)`/).flatten
    [workflow, agents.uniq]
  end
end

def validate_semantics(findings, cleared)
  levels = {
    "new-component" => "mini",
    "refactor-component" => "mini",
    "fix-pr-comments" => "mini",
    "new-view" => "standard",
    "new-feature" => "full",
    "refactor-feature" => "full",
    "test-plan" => "full"
  }
  templates = levels.values.uniq.to_h do |level|
    [level, read_yaml("chapters/mobile/docs/templates/spec-packets/#{level}-spec.yaml")]
  end
  schema = read_yaml("chapters/mobile/docs/templates/schemas/mobile-spec.schema.yaml")
  context_schema = JSON.parse(File.read("chapters/mobile/docs/templates/schemas/mobile-context.schema.json"))
  context_template = JSON.parse(File.read("chapters/mobile/docs/templates/spec-packets/context.json"))
  bootstrap_schema = read_yaml("chapters/mobile/docs/templates/schemas/bootstrap-spec.schema.yaml")
  project_config = read_yaml("chapters/mobile/docs/templates/project.config.yaml")
  architecture_contract = read_yaml("chapters/mobile/docs/templates/architecture-contract.yaml")
  dependencies_contract = read_yaml("chapters/mobile/docs/templates/dependencies-contract.yaml")
  known_agents = Dir["chapters/mobile/agents/_all/*.agent.md"].map { |p| File.basename(p, ".agent.md") }

  required_context_fields = %w[
    schema_version schema_ref run_id workflow spec_level workflow_controller status
    packet_owner_target_id packet_root current_phase checkpoints completed_phases phase_results artifacts
  ]
  missing_context_fields = required_context_fields.reject { |field| context_template.key?(field) }
  unless missing_context_fields.empty?
    add(findings, "CRITICAL", "CONTEXT_TEMPLATE_FIELDS_MISSING", "context.json template is missing required state fields", missing_context_fields.join(", "))
  end
  unless context_template["schema_ref"]&.end_with?("mobile-context.schema.json")
    add(findings, "CRITICAL", "CONTEXT_SCHEMA_REF_MISSING", "context.json template must reference mobile-context.schema.json")
  end
  context_schema_required = context_schema["required"] || []
  %w[packet_owner_target_id packet_root].each do |field|
    next if context_schema_required.include?(field)

    add(findings, "CRITICAL", "CONTEXT_PACKET_OWNER_FIELDS_MISSING", "mobile context schema must require packet ownership fields", field)
  end
  unless context_template.dig("checkpoints", "initial_spec", "status") == "pending"
    add(findings, "CRITICAL", "CONTEXT_INITIAL_CHECKPOINT_MISSING", "context.json template must initialize the initial_spec checkpoint as pending")
  end
  unless (context_schema.dig("properties", "status", "enum") || []).include?("approved_for_execution")
    add(findings, "CRITICAL", "CONTEXT_APPROVAL_STATE_MISSING", "mobile context schema must allow approved_for_execution")
  end

  example_contexts = Dir["chapters/mobile/examples/spec-packets/*/*/context.json"]
  example_contexts.each do |path|
    context = JSON.parse(File.read(path))
    missing = required_context_fields.reject { |field| context.key?(field) }
    unless missing.empty?
      add(findings, "HIGH", "CONTEXT_EXAMPLE_FIELDS_MISSING", "#{path} is missing required context fields", missing.join(", "))
      next
    end
    unless context["schema_ref"].to_s.end_with?("mobile-context.schema.json")
      add(findings, "HIGH", "CONTEXT_EXAMPLE_SCHEMA_REF_MISSING", "#{path} must reference mobile-context.schema.json")
    end
    unless context["checkpoints"].is_a?(Hash) && context.dig("checkpoints", "initial_spec", "status") == "pending"
      add(findings, "HIGH", "CONTEXT_EXAMPLE_CHECKPOINT_INVALID", "#{path} must use an initial_spec checkpoint object")
    end
    unless context["artifacts"].is_a?(Hash)
      add(findings, "HIGH", "CONTEXT_EXAMPLE_ARTIFACTS_INVALID", "#{path} artifacts must be an object keyed by artifact group")
    end
  end

  legacy_config_files = %w[
    ARCHITECTURE-CONTRACT.yaml
    DEPENDENCIES-CONTRACT.yaml
    PROJECT-CONFIG-GUIDE.md
  ]
  template_dir_entries = Dir.children("chapters/mobile/docs/templates")
  legacy_config_files.each do |file|
    if template_dir_entries.include?(file)
      add(findings, "HIGH", "LEGACY_CONFIG_FILENAME", "Legacy uppercase template filename found", file)
    end
  end

  {
    "architecture-contract.yaml" => architecture_contract,
    "dependencies-contract.yaml" => dependencies_contract
  }.each do |expected_file, yaml|
    actual = yaml.dig("ownership", "file")
    next if actual == expected_file

    add(
      findings,
      "HIGH",
      "CONFIG_OWNERSHIP_FILENAME_DRIFT",
      "#{expected_file} ownership.file must match the lowercase filename",
      "actual=#{actual.inspect}"
    )
  end

  if project_config.key?("structure")
    add(
      findings,
      "HIGH",
      "PROJECT_CONFIG_TOP_LEVEL_STRUCTURE",
      "project.config.yaml must not define top-level structure; use targets.registry.<target_id>.structure"
    )
  end

  %w[generation_scope contracts_policy].each do |field|
    next unless project_config.dig("pipeline", field)

    add(
      findings,
      "HIGH",
      "PROJECT_CONFIG_ARCHITECTURE_POLICY_DRIFT",
      "project.config.yaml pipeline.#{field} duplicates architecture-contract.yaml generation policies"
    )
  end

  if project_config.dig("architecture", "require_contract_for_new_view")
    add(
      findings,
      "HIGH",
      "PROJECT_CONFIG_ARCHITECTURE_POLICY_DRIFT",
      "project.config.yaml architecture.require_contract_for_new_view belongs in architecture-contract.yaml"
    )
  end

  if project_config.dig("tokens", "extension_import")
    add(
      findings,
      "HIGH",
      "PROJECT_CONFIG_IMPORT_DRIFT",
      "project.config.yaml tokens.extension_import duplicates dependency import ownership"
    )
  end

  target_imports = []
  (project_config.dig("targets", "registry") || {}).each do |target_id, target|
    target_imports << "#{target_id}.import" if target.key?("import")
  end
  if target_imports.any?
    add(
      findings,
      "HIGH",
      "PROJECT_CONFIG_IMPORT_DRIFT",
      "project.config.yaml targets must not define package imports; use dependencies-contract.yaml",
      target_imports.join("\n")
    )
  end

  executing_agents_by_workflow.each do |workflow, agents|
    next unless levels[workflow]

    permissions = templates[levels[workflow]]["agent_permissions"] || {}
    agents.each do |agent|
      next unless known_agents.include?(agent)
      next if permissions.key?(agent)

      add(
        findings,
        "CRITICAL",
        "PERMISSION_MISSING",
        "#{workflow} executes #{agent}, but #{levels[workflow]}-spec has no permissions for it",
        "workflow=#{workflow}, agent=#{agent}"
      )
    end
  end

  %w[external_access agent_permissions evidence_mode].each do |field|
    next if (schema["required"] || []).include?(field)

    add(findings, "CRITICAL", "SCHEMA_REQUIRED_MISSING", "mobile-spec.schema.yaml does not require #{field}")
  end

  evidence_mode_property = schema.dig("properties", "evidence_mode") || {}
  unless evidence_mode_property["enum"] == %w[minimal standard] && evidence_mode_property["default"] == "minimal"
    add(findings, "CRITICAL", "EVIDENCE_MODE_SCHEMA_DRIFT", "mobile-spec.schema.yaml must define minimal and standard evidence modes with minimal default")
  end
  unless (bootstrap_schema["required"] || []).include?("evidence_mode") &&
         bootstrap_schema.dig("properties", "evidence_mode", "default") == "minimal"
    add(findings, "CRITICAL", "BOOTSTRAP_EVIDENCE_MODE_SCHEMA_DRIFT", "bootstrap schema must require evidence_mode with minimal default")
  end
  levels.each do |workflow, level|
    template_mode = templates[level]["evidence_mode"]
    unless template_mode == "minimal"
      add(findings, "CRITICAL", "EVIDENCE_MODE_TEMPLATE_DRIFT", "#{level}-spec must default evidence_mode to minimal", "workflow=#{workflow}")
    end
    overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/#{workflow}.yaml")
    unless (overlay["optional_inputs"] || []).include?("evidence_mode")
      add(findings, "CRITICAL", "EVIDENCE_MODE_INPUT_MISSING", "#{workflow} overlay must declare optional evidence_mode")
    end
    text = File.read("chapters/mobile/workflows/_all/#{workflow}.workflow.md")
    unless text.match?(/evidence_mode/i) && text.include?("phase_results")
      add(findings, "CRITICAL", "EVIDENCE_MODE_WORKFLOW_DRIFT", "#{workflow} must define evidence_mode and compact phase results")
    end
  end
  bootstrap_overlay_for_evidence = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/bootstrap-workspace.yaml")
  bootstrap_template = read_yaml("chapters/mobile/docs/templates/bootstrap/bootstrap-spec.yaml")
  bootstrap_workflow_for_evidence = File.read("chapters/mobile/workflows/_all/bootstrap-workspace.workflow.md")
  unless (bootstrap_overlay_for_evidence["optional_inputs"] || []).include?("evidence_mode") &&
         bootstrap_template["evidence_mode"] == "minimal" &&
         bootstrap_workflow_for_evidence.match?(/evidence_mode/i) &&
         bootstrap_workflow_for_evidence.include?("phase_results")
    add(findings, "CRITICAL", "BOOTSTRAP_EVIDENCE_MODE_DRIFT", "bootstrap resources must support minimal and standard evidence modes")
  end

  enum_groups = schema.dig("properties", "artifact_plan", "properties", "planned", "items", "properties", "group", "enum") || []
  used_groups = Dir["chapters/mobile/workflows/_all/*.workflow.md"].flat_map do |path|
    text = File.read(path)
    text.scan(/artifact_plan\.planned\[group=([a-z_]+)\]/).flatten +
      text.scan(/group:\s*([a-z_]+)/).flatten
  end.uniq
  (used_groups - enum_groups).each do |group|
    add(findings, "HIGH", "ARTIFACT_GROUP_UNKNOWN", "Workflow uses artifact group not allowed by schema", group)
  end

  %w[new-component new-view new-feature].each do |workflow|
    overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/#{workflow}.yaml")
    level = overlay["base_spec_level"]
    figma = overlay.dig("required_external_access", "figma_mcp") || {}
    preflight_agent = figma["preflight_agent"]

    unless preflight_agent == "figma-analyzer"
      add(findings, "CRITICAL", "FIGMA_PREFLIGHT_OWNER_DRIFT", "#{workflow} must assign Figma preflight to figma-analyzer", "actual=#{preflight_agent.inspect}")
      next
    end

    tools = templates[level].dig("agent_permissions", preflight_agent, "can_call_external_tools") || []
    unless tools.include?("figma_mcp")
      add(findings, "CRITICAL", "FIGMA_PREFLIGHT_PERMISSION", "#{workflow} preflight agent lacks figma_mcp", "agent=#{preflight_agent}")
    end
    preflight_evidence = templates[level].dig("agent_permissions", preflight_agent, "evidence_required") || []
    unless preflight_evidence.include?("evidence/figma-mcp-preflight.md")
      add(findings, "CRITICAL", "FIGMA_PREFLIGHT_EVIDENCE_MISSING", "#{workflow} preflight agent must require compact Figma preflight evidence")
    end

    workflow_text = File.read("chapters/mobile/workflows/_all/#{workflow}.workflow.md")
    unless workflow_text.include?("@figma-analyzer")
      add(findings, "HIGH", "FIGMA_ANALYZER_DELEGATION_MISSING", "#{workflow} does not delegate Figma work to figma-analyzer")
    end
  end

  %w[mini standard full].each do |level|
    ds_tools = templates[level].dig("agent_permissions", "ds-orchestrator", "can_call_external_tools") || []
    if ds_tools.include?("figma_mcp")
      add(findings, "HIGH", "FIGMA_CONTROLLER_PERMISSION_DRIFT", "#{level}-spec grants figma_mcp to ds-orchestrator; only figma-analyzer may call Figma MCP")
    end
  end

  controller_context_sections = %w[
    context.json.status context.json.current_phase context.json.checkpoints
  ]
  controller_context_sections << "context.json.phase_results"
  {
    "mini" => ["ds-orchestrator"],
    "standard" => ["ds-orchestrator"],
    "full" => %w[feature-builder refactoring-advisor test-coverage-engineer]
  }.each do |level, controllers|
    controllers.each do |controller|
      sections = templates[level].dig("agent_permissions", controller, "can_write", "context_sections") || []
      missing = controller_context_sections - sections
      next if missing.empty?

      add(findings, "CRITICAL", "CONTROLLER_CONTEXT_PERMISSION_MISSING", "#{controller} cannot manage required context state in #{level}-spec", missing.join(", "))
    end
  end

  unless project_config.dig("targets", "registry", "project_docs")
    add(findings, "CRITICAL", "PROJECT_DOCS_TARGET_MISSING", "project.config template has no project_docs target")
  end

  full_spec = templates["full"]
  if (full_spec["agent_permissions"] || {}).key?("documentation-projects")
    add(findings, "HIGH", "DOCS_ACTOR_DRIFT", "full-spec models documentation-projects as an actor instead of a shared skill")
  end

  new_feature_overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/new-feature.yaml")
  new_feature_workflow = File.read("chapters/mobile/workflows/_all/new-feature.workflow.md")
  master_orchestration = File.read("chapters/mobile/prompts/_all/master-orchestration.prompt.md")
  test_generation = File.read("chapters/mobile/prompts/_all/test-generation.prompt.md")
  test_engineer = File.read("chapters/mobile/agents/_all/test-engineer.agent.md")
  golden_test_engineer = File.read("chapters/mobile/agents/_all/golden-test-engineer.agent.md")
  delivery_manager = File.read("chapters/mobile/agents/_all/delivery-manager.agent.md")
  ds_orchestrator = File.read("chapters/mobile/agents/_all/ds-orchestrator.agent.md")

  %w[golden_tests documentation].each do |input|
    unless (new_feature_overlay["optional_inputs"] || []).include?(input)
      add(findings, "CRITICAL", "NEW_FEATURE_OPTION_INPUT_MISSING", "new-feature overlay must declare optional #{input}")
    end
    property = schema.dig("properties", "inputs", "properties", input) || {}
    unless property["type"] == "boolean" && property["default"] == false
      add(findings, "CRITICAL", "NEW_FEATURE_OPTION_SCHEMA_DRIFT", "mobile-spec schema must define #{input} as boolean default false")
    end
  end

  %w[unit_tests widget_tests integration_tests].each do |group|
    unless (new_feature_overlay["artifact_groups"] || []).include?(group)
      add(findings, "CRITICAL", "NEW_FEATURE_TEST_GROUP_MISSING", "new-feature overlay must declare #{group}")
    end
    unless new_feature_workflow.include?("artifact_plan.planned[group=#{group}]")
      add(findings, "CRITICAL", "NEW_FEATURE_TEST_PLAN_MISSING", "new-feature workflow must require planned #{group} artifacts")
    end
  end

  %w[test-engineer delivery-manager].each do |agent|
    unless (new_feature_overlay["required_agents"] || []).include?(agent)
      add(findings, "CRITICAL", "NEW_FEATURE_AGENT_MISSING", "new-feature overlay must require #{agent}")
    end
    unless full_spec.dig("agent_permissions", agent)
      add(findings, "CRITICAL", "NEW_FEATURE_PERMISSION_MISSING", "full-spec must grant #{agent} permissions for new-feature")
    end
  end

  unless (new_feature_overlay.dig("conditional_agents", "golden_tests") || []).include?("golden-test-engineer")
    add(findings, "CRITICAL", "NEW_FEATURE_GOLDEN_AGENT_DRIFT", "new-feature must make golden-test-engineer conditional on golden_tests")
  end

  %w[FEATURE_UNIT_TESTS FEATURE_WIDGET_TESTS FEATURE_INTEGRATION_TESTS].each do |mode|
    [new_feature_workflow, master_orchestration, test_generation, test_engineer].each_with_index do |text, index|
      next if text.include?(mode)

      source = %w[new-feature-workflow master-orchestration test-generation test-engineer][index]
      add(findings, "CRITICAL", "NEW_FEATURE_TEST_MODE_DRIFT", "#{source} must define #{mode}")
    end
  end

  %w[FEATURE_GOLDEN_TESTS golden_tests=true documentation=true skipped_by_input].each do |required|
    unless new_feature_workflow.include?(required)
      add(findings, "CRITICAL", "NEW_FEATURE_OPTIONAL_STAGE_DRIFT", "new-feature workflow must define #{required}")
    end
  end

  unless test_generation.include?("FEATURE_GOLDEN_TESTS") && golden_test_engineer.include?("FEATURE_GOLDEN_TESTS")
    add(findings, "CRITICAL", "NEW_FEATURE_GOLDEN_MODE_DRIFT", "Golden resources must define FEATURE_GOLDEN_TESTS")
  end

  {
    "new-component" => {
      level: "mini",
      modes: %w[DS_GOLDEN_TESTS],
      required_evidence: %w[evidence/widget-tests.md]
    },
    "new-view" => {
      level: "standard",
      modes: %w[DS_GOLDEN_TESTS VIEW_GOLDEN_TESTS],
      required_evidence: %w[evidence/widget-tests.md evidence/view-widget-tests.md]
    }
  }.each do |workflow, contract|
    overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/#{workflow}.yaml")
    workflow_text = File.read("chapters/mobile/workflows/_all/#{workflow}.workflow.md")

    unless (overlay["optional_inputs"] || []).include?("golden_tests")
      add(findings, "CRITICAL", "OPTIONAL_GOLDEN_INPUT_MISSING", "#{workflow} overlay must declare optional golden_tests")
    end
    unless (overlay.dig("conditional_agents", "golden_tests") || []).include?("golden-test-engineer")
      add(findings, "CRITICAL", "OPTIONAL_GOLDEN_AGENT_DRIFT", "#{workflow} must make golden-test-engineer conditional on golden_tests")
    end
    unless templates[contract[:level]].dig("agent_permissions", "golden-test-engineer")
      add(findings, "CRITICAL", "OPTIONAL_GOLDEN_PERMISSION_MISSING", "#{contract[:level]}-spec must grant golden-test-engineer permissions")
    end
    %w[golden_tests=true golden_tests=false skipped_by_input].each do |required|
      unless workflow_text.include?(required)
        add(findings, "CRITICAL", "OPTIONAL_GOLDEN_WORKFLOW_DRIFT", "#{workflow} workflow must define #{required}")
      end
    end
    contract[:modes].each do |mode|
      [workflow_text, master_orchestration, ds_orchestrator, golden_test_engineer].each_with_index do |text, index|
        next if text.include?(mode)

        source = %W[#{workflow}-workflow master-orchestration ds-orchestrator golden-test-engineer][index]
        add(findings, "CRITICAL", "OPTIONAL_GOLDEN_MODE_DRIFT", "#{source} must define #{mode}")
      end
    end
    contract[:required_evidence].each do |evidence|
      unless delivery_manager.include?(evidence)
        add(findings, "CRITICAL", "OPTIONAL_GOLDEN_DELIVERY_GATE_MISSING", "delivery-manager must require #{evidence} for #{workflow}")
      end
    end
  end

  %w[evidence/unit-tests.md evidence/widget-tests.md evidence/integration-tests.md].each do |evidence|
    unless delivery_manager.include?(evidence)
      add(findings, "CRITICAL", "NEW_FEATURE_DELIVERY_GATE_MISSING", "delivery-manager must require #{evidence}")
    end
  end

  %w[feature-builder refactoring-advisor test-coverage-engineer].each do |agent|
    targets = full_spec.dig("agent_permissions", agent, "can_write", "artifact_targets") || []
    next if targets.any? { |target| target.to_s.include?("PROJECT_DOCS") || target.to_s.include?("project_docs") }

    add(findings, "HIGH", "DOCS_TARGET_PERMISSION_MISSING", "#{agent} cannot write docs target in full-spec")
  end

  %w[new-feature refactor-feature test-plan].each do |workflow|
    text = File.read("chapters/mobile/workflows/_all/#{workflow}.workflow.md")
    next if text.include?("group: docs")

    add(findings, "CRITICAL", "DOCS_NOT_PLANNED", "#{workflow} lacks artifact_plan.planned[group=docs] requirement")
  end

  %w[new-feature fix-pr-comments].each do |workflow|
    text = File.read("chapters/mobile/workflows/_all/#{workflow}.workflow.md")
    next if text.include?("does not run `git`") || text.include?("no ejecuta `git`")

    add(findings, "HIGH", "DELIVERY_GIT_AMBIGUOUS", "#{workflow} can be read as executing git without permissions")
  end

  refactor_text = File.read("chapters/mobile/workflows/_all/refactor-feature.workflow.md")
  unless refactor_text.include?("can_delete_files=true") && refactor_text.include?("action: delete")
    add(findings, "HIGH", "DELETE_ELEVATION_MISSING", "refactor-feature lacks delete elevation rule")
  end

  unless bootstrap_schema.to_s.include?("applied") &&
         bootstrap_schema.to_s.include?("target_registry_paths_resolved") &&
         bootstrap_schema.to_s.include?("const")
    add(findings, "MEDIUM", "BOOTSTRAP_APPLIED_FLAGS", "bootstrap schema does not force critical flags when status=applied")
  end

  bootstrap_workflow = File.read("chapters/mobile/workflows/_all/bootstrap-workspace.workflow.md")
  workspace_agent = File.read("chapters/mobile/agents/_all/workspace-discovery.agent.md")
  workspace_prompt = File.read("chapters/mobile/prompts/_all/workspace-discovery.prompt.md")
  ds_orchestrator = File.read("chapters/mobile/agents/_all/ds-orchestrator.agent.md")
  new_view_workflow = File.read("chapters/mobile/workflows/_all/new-view.workflow.md")
  new_view_overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/new-view.yaml")
  bootstrap_overlay = read_yaml("chapters/mobile/docs/templates/spec-packets/overlays/bootstrap-workspace.yaml")

  [bootstrap_workflow, workspace_agent, workspace_prompt].each_with_index do |text, index|
    source = %w[bootstrap-workflow workspace-agent workspace-prompt][index]
    %w[reused_existing_config CONFIG_BOOTSTRAP_INCOMPLETE CONFIG_BOOTSTRAP_CONFIG_INVALID FORCE_RECONFIGURE].each do |required|
      next if text.include?(required)

      add(findings, "HIGH", "BOOTSTRAP_REUSE_GUARD_MISSING", "#{source} must define bootstrap reuse/repair behavior", required)
    end
  end

  unless ds_orchestrator.include?("Do not invoke `/bootstrap-workspace` automatically") &&
         ds_orchestrator.include?("CONFIG_LEGACY_COPILOT_CONFIGURATION_FOUND")
    add(findings, "HIGH", "FUNCTIONAL_BOOTSTRAP_AUTORUN", "ds-orchestrator must block instead of auto-running bootstrap and reject legacy config")
  end

  unless new_view_workflow.include?("This workflow never starts bootstrap automatically") &&
         new_view_workflow.include?("project_root")
    add(findings, "HIGH", "NEW_VIEW_CONFIG_GATE_MISSING", "new-view must have an explicit canonical-config gate and project_root override")
  end

  unless (new_view_overlay["optional_inputs"] || []).include?("project_root")
    add(findings, "HIGH", "NEW_VIEW_PROJECT_ROOT_INPUT_MISSING", "new-view overlay must declare project_root as an optional input")
  end

  packet_owner = new_view_overlay["spec_packet_owner"] || {}
  unless packet_owner["target_resolution"] == "input.target_id_or_active_target_defaults.app_target_id" &&
         packet_owner["fallback_key"] == "active_target_defaults.app" &&
         packet_owner["required_kind"] == "app" &&
         packet_owner["immutable_across_phases"] == true
    add(findings, "CRITICAL", "NEW_VIEW_PACKET_OWNER_CONTRACT_MISSING", "new-view overlay must define an immutable app-owned packet", packet_owner.inspect)
  end

  unless (bootstrap_overlay["optional_inputs"] || []).include?("force_reconfigure")
    add(findings, "HIGH", "BOOTSTRAP_FORCE_RECONFIGURE_INPUT_MISSING", "bootstrap overlay must declare force_reconfigure as an optional input")
  end

  widget_developer = File.read("chapters/mobile/agents/_all/widget-developer.agent.md")
  codegen_view = File.read("chapters/mobile/prompts/_all/codegen-view.prompt.md")
  master_orchestration = File.read("chapters/mobile/prompts/_all/master-orchestration.prompt.md")
  spec_validation_skill = File.read("chapters/mobile/skills/_all/mobile-sdd-spec-validation/SKILL.md")

  unless ds_orchestrator.include?("Non-Negotiable `/new-view` Start Gate") &&
         ds_orchestrator.include?("The first `/new-view` invocation is plan-only")
    add(findings, "CRITICAL", "NEW_VIEW_PLAN_ONLY_GATE_MISSING", "ds-orchestrator must make the first new-view invocation plan-only")
  end

  unless new_view_workflow.include?("Initial Invocation Is Plan-Only") &&
         new_view_workflow.include?("response that presents this review must end here")
    add(findings, "CRITICAL", "NEW_VIEW_REVIEW_STOP_GATE_MISSING", "new-view must stop after presenting the initial review")
  end

  unless new_view_workflow.include?("SPEC_PACKET_OWNER_TARGET_ID = APP_TARGET_ID") &&
         new_view_workflow.include?("CONFIG_SPEC_PACKET_ROOT_MISMATCH") &&
         new_view_workflow.include?("all packet state and evidence under this app-owned packet")
    add(findings, "CRITICAL", "NEW_VIEW_PACKET_OWNER_GATE_MISSING", "new-view must keep packet state in the immutable app-owned root")
  end

  new_view_support = {
    "ds-orchestrator" => ds_orchestrator,
    "component-planner" => File.read("chapters/mobile/agents/_all/component-planner.agent.md"),
    "delivery-manager" => File.read("chapters/mobile/agents/_all/delivery-manager.agent.md"),
    "widgetbook-developer" => File.read("chapters/mobile/agents/_all/widgetbook-developer.agent.md"),
    "codegen-view" => codegen_view
  }
  target_alias_misses = new_view_support.select do |_name, text|
    text.include?("targets.registry[app]")
  end.keys
  unless target_alias_misses.empty?
    add(findings, "CRITICAL", "NEW_VIEW_APP_TARGET_ALIAS_DRIFT", "new-view resources must resolve the configured app target instead of a literal app alias", target_alias_misses.join(", "))
  end

  delivery_manager = new_view_support.fetch("delivery-manager")
  unless delivery_manager.include?("SPEC_PACKET_OWNER_ROOT") &&
         !delivery_manager.include?("PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}")
    add(findings, "CRITICAL", "NEW_VIEW_DELIVERY_PACKET_ROOT_DRIFT", "delivery manager must preserve the packet-owner root")
  end

  [widget_developer, codegen_view].each_with_index do |text, index|
    source = %w[widget-developer codegen-view][index]
    %w[approved_for_execution CONFIG_SPEC_NOT_APPROVED].each do |required|
      next if text.include?(required)

      add(findings, "CRITICAL", "CODEGEN_APPROVAL_GATE_MISSING", "#{source} must reject codegen before spec approval", required)
    end
  end

  unless master_orchestration.include?("initial functional invocation as plan-only") &&
         master_orchestration.include?("response that presents `review.md` must end") &&
         !master_orchestration.include?("PROJECT_CONFIG_BOOT_PATH")
    add(findings, "HIGH", "MASTER_PLAN_ONLY_GATE_MISSING", "master orchestration must preserve the plan-only first invocation")
  end

  unless master_orchestration.include?("SPEC_PACKET_OWNER_TARGET_ID") &&
         master_orchestration.include?("must never move\n     packet state or evidence") &&
         master_orchestration.include?("Do not derive `SPEC_PACKET_ROOT`")
    add(findings, "CRITICAL", "MASTER_PACKET_OWNER_GATE_MISSING", "master orchestration must separate immutable packet ownership from active phase targets")
  end

  unless spec_validation_skill.include?("`/new-view` Plan Gate") &&
         spec_validation_skill.include?("Non-empty `canonical_spec`") &&
         spec_validation_skill.include?("packet_owner_target_id")
    add(findings, "HIGH", "NEW_VIEW_PLAN_VALIDATION_MISSING", "spec validation skill must require a complete new-view plan before approval")
  end

  cleared << "Semantic workflow/template/schema checks passed" unless findings.any?
end

def validate_language_policy(findings, cleared)
  spanish_markers = /
    \b(
      Agente|Fase|Validar|Crear|Debe|Reglas|Prerrequisitos|Entrada|Salida|
      Validacion|Validación|Permisos|obligatorio|bloquear|configuracion|
      configuración|arquitectura|dependencias|flujo|humano|documentacion|
      documentación|evidencia|aprobacion|aprobación|correcciones|Entrega|
      Accion|Acción|Topologia|Topología|Detectada|Propuesta|
      verificar|llamar|delegar|delega|funcionales|distintos|enviar|
      permitirlo|tras|pregunta|audites|acceso|escribe|condicional|
      impacto|marque|acumulativo|proposeds|candidata|opcionalmente|
      ver|consulta|ruta|compartido|cuando|mantiene|estado|correcta|
      activar|navegar|perder|orquestador|condicionales|especiales|obvios|
      disponible|devolver|anotaciones
    )\b
  /x

  known_bad_language_artifacts = {
    "createstion" => /createstion/,
    "generatesting" => /generatesting/,
    "TaskEither.trandCatch" => /TaskEither\.trandCatch/,
    "rthisrtable()" => /rthisrtable\(\)/,
    "user storyMAN" => /user storyMAN/,
    "structureda" => /structureda/,
    "bandpass" => /bandpass/,
    "No se generates" => /No se generates/,
    "this configured" => /this configured/,
    "there are complete test coverage" => /there are complete test coverage/,
    "there are a Figma" => /there are a Figma/,
    "there are its own" => /there are its own/,
    "file there are ZERO" => /file there are ZERO/,
    "responde for the frame main" => /responde for the frame main/,
    "marque the spec como approved" => /marque the spec como approved/,
    "report acumulativo" => /report acumulativo/,
    "Refactorizar" => /Refactorizar/,
    "Nuevo Component" => /Nuevo Component/,
    "Nueva View" => /Nueva View/,
    "Secuencia Canonical" => /Secuencia Canonical/,
    "Apply Cambios" => /Apply Cambios/,
    "Restringir changes" => /Restringir changes/,
    "haand" => /haand/,
    "beforel" => /beforel/,
    "generatesl" => /generatesl/,
    "doc-generatestor" => /doc-generatestor/,
    "Pandramid" => /pandramid/i,
    "standling" => /standling/i,
    "Cothem" => /cothem/i,
    "tandping" => /tandping/i,
    "Analandze" => /analandze/i,
    "tor typo" => /\btor\b/i,
    "dor typo" => /\bdor\b/i,
    "Spanish feature target" => /feature indicado/i,
    "If not contract" => /If not contract/,
    "MCP Figma" => /MCP Figma/,
    "canonical route" => /canonical route/,
    "checkpoint required of layer" => /checkpoint required of layer/
  }

  allowed_paths = [
    %r{\Achapters/mobile/docs/templates/.*/review\.md\z},
    %r{\Achapters/mobile/docs/templates/spec-packets/review\.md\z}
  ]

  allowed_line_patterns = [
    /Spanish/,
    /Spanish-speaking/,
    /Spanish human-facing/,
    /in Spanish/,
    /review\.md/,
    /apruebo aplicar/,
    /Propuesta de Bootstrap/,
    /Topologia Detectada/,
    /Archivos Que Se Proponen/,
    /Decisiones Importantes/,
    /Accion Requerida/
  ]

  hits = []
  quality_hits = []
  files = Dir[
    "chapters/mobile/{docs,workflows,steering,agents,prompts,skills}/**/*.{md,yaml,yml,json}"
  ].select { |path| File.file?(path) }

  files.each do |path|
    next if allowed_paths.any? { |pattern| path.match?(pattern) }

    in_fenced_block = false
    File.readlines(path, chomp: true).each_with_index do |line, index|
      if line.strip.start_with?("```")
        in_fenced_block = !in_fenced_block
        next
      end
      next if in_fenced_block

      known_bad_language_artifacts.each do |label, pattern|
        quality_hits << "#{path}:#{index + 1}: #{label}: #{line.strip}" if line.match?(pattern)
      end

      next unless line.match?(spanish_markers)
      next if allowed_line_patterns.any? { |pattern| line.match?(pattern) }

      hits << "#{path}:#{index + 1}: #{line.strip}"
    end
  end

  if quality_hits.any?
    add(
      findings,
      "HIGH",
      "LANGUAGE_QUALITY_DRIFT",
      "Known hybrid-language or typo artifacts found in internal KB assets",
      quality_hits.first(120).join("\n")
    )
  end

  if hits.empty?
    cleared << "Language policy passed for internal KB assets" if quality_hits.empty?
  elsif STRICT_LANGUAGE
    add(
      findings,
      "HIGH",
      "INTERNAL_LANGUAGE_DRIFT",
      "Spanish prose found in internal KB assets outside allowed human-facing surfaces",
      hits.first(120).join("\n")
    )
  else
    cleared << "Language policy audit skipped; run with --strict-language to enforce English-only internal KB"
  end
end

parse_all_structured_files(findings, cleared)
validate_no_legacy_refs(findings, cleared)
validate_no_source_root_refs(findings, cleared)
validate_references(findings, cleared)
validate_workflow_steering_sync(findings, cleared)
validate_invocation_contracts(findings, cleared)
validate_semantics(findings, cleared)
validate_language_policy(findings, cleared)

if findings.empty?
  puts "Mobile KB validation OK"
  cleared.each { |item| puts "- #{item}" }
  exit 0
end

puts "Mobile KB validation failed"
findings.each do |finding|
  puts "[#{finding.severity}] #{finding.id}: #{finding.message}"
  puts finding.evidence unless finding.evidence.to_s.empty?
end
exit 1
