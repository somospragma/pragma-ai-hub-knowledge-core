# frozen_string_literal: true

# Tests for the Workflow Response Contract validator helpers defined in
# validate_mobile_kb.rb. These tests exercise the pure helper functions on
# in-memory strings so we can assert every failure branch deterministically,
# without shelling out to the whole validator.

require "minitest/autorun"

# Load the validator script for its helper definitions. The script also runs
# its main block against the whole KB when required directly, which would
# pollute test output and fail if the KB has any real issue. Load it as a
# module-like source by evaluating only the top of the file up to the main
# invocation block.

VALIDATOR_PATH = File.expand_path("validate_mobile_kb.rb", __dir__)
VALIDATOR_SOURCE = File.read(VALIDATOR_PATH)
# Anchor uniquely on the sequence of top-level invocations at the end of the
# file (the definition of parse_all_structured_files appears earlier).
MAIN_MARKER = "parse_all_structured_files(findings, cleared)\nvalidate_no_legacy_refs"
HELPERS_SOURCE = VALIDATOR_SOURCE.split(MAIN_MARKER, 2).first
raise "cannot locate validator main marker" if HELPERS_SOURCE == VALIDATOR_SOURCE

# Stub `add` so the validate function does not require the outer Finding
# struct plumbing when the tests instantiate it directly.
Finding = Struct.new(:severity, :id, :message, :evidence, keyword_init: true) unless defined?(Finding)

# Evaluate helpers at the top level so their `def` statements install into
# the current test process.
Object.class_eval(HELPERS_SOURCE)

class WorkflowResponseContractHelpersTest < Minitest::Test
  RESPONSE_CONTRACT_BLOCK = <<~MD
    > ### ▶ Response Contract (non-negotiable)
    >
    > Your response for this phase MUST, in order:
    >
    > 1. Emit the `--status started` command below.
    > 2. Do the work.
    > 3. Emit the terminal status command.
    > 4. Run the gap report.
    > 5. End your response with the prompt below and yield.
    >
    > ```
    > He completado PHASE 0 — Something. ¿Apruebas el resultado?
    >   1. ✅ Aprobado — continuar
    >   2. ✏️ Ediciones — dime qué cambiar
    >   3. ❌ Rechazado — regenerar desde cero
    > ```
    >
    > Silence is not approval.
  MD

  STARTED_BASH = <<~MD
    > ⚡ **EXECUTE NOW** — Run the command below via your shell tool.

    ```bash
    pragma-ai workflow report \\
      --instance-id "$INSTANCE_ID" \\
      --workflow-id my-workflow \\
      --step-id phase-0-x \\
      --status started
    ```
  MD

  FINISHED_BASH = <<~MD
    > ⚡ **EXECUTE NOW (success path)** — Run the command below.

    ```bash
    pragma-ai workflow report \\
      --instance-id "$INSTANCE_ID" \\
      --workflow-id my-workflow \\
      --step-id phase-0-x \\
      --status finished \\
      --output-file "path/to/artifact.md"
    ```
  MD

  def build_phase(heading, body_extras: "")
    <<~MD
      ### #{heading}

      #{RESPONSE_CONTRACT_BLOCK}
      #{STARTED_BASH}
      #{FINISHED_BASH}
      #{body_extras}
    MD
  end

  def build_workflow(id:, step_ids:, phases:)
    step_ids_row = "| Step IDs | #{step_ids.map { |s| "`#{s}`" }.join(', ')} |"
    <<~MD
      ---
      id: #{id}
      version: 1.0.0
      scope: chapter
      type: workflow
      chapter: mobile
      ---
      # Workflow: Test

      ## Telemetry — Workflow metadata

      | Field | Value |
      |---|---|
      | `workflow-id` | `#{id}` |
      #{step_ids_row}

      ## Workflow Execution Contract

      Reglas.

      ## Instructions to the executing agent

      Instrucciones.

      #{phases.join("\n---\n")}

      ## Response Contract Violations

      Violaciones.

      ## Human approval gate

      Gate.
    MD
  end

  def test_workflow_step_ids_from_header_extracts_ids
    text = "| Step IDs | `phase-a`, `phase-b`, `phase-c` |\n"
    assert_equal %w[phase-a phase-b phase-c], workflow_step_ids_from_header(text)
  end

  def test_workflow_step_ids_returns_empty_when_missing
    assert_equal [], workflow_step_ids_from_header("no table here")
  end

  def test_workflow_phase_sections_detects_phase_gate_and_checkpoint
    md = <<~MD
      # Title

      ## Preamble

      Content.

      ### PHASE 0 — Alpha

      Body A.

      ### Gate 1 — Beta

      Body B.

      ### HUMAN CHECKPOINT — Gamma

      Body C.

      ## Not a phase

      Ignored.
    MD

    sections = workflow_phase_sections(md)
    assert_equal 3, sections.size
    assert_equal "PHASE 0 — Alpha", sections[0][:heading]
    assert_equal "Gate 1 — Beta", sections[1][:heading]
    assert_equal "HUMAN CHECKPOINT — Gamma", sections[2][:heading]
  end

  def test_workflow_phase_sections_detects_h2_gate_required
    md = <<~MD
      # Title

      ## Topology Gate (required)

      Body A.

      ## Not a phase

      Ignored.
    MD

    sections = workflow_phase_sections(md)
    assert_equal 1, sections.size
    assert_equal "Topology Gate (required)", sections[0][:heading]
  end

  def test_bash_report_calls_extracts_step_id_workflow_id_status
    body = <<~MD
      ```bash
      pragma-ai workflow report \\
        --instance-id "$INSTANCE_ID" \\
        --workflow-id my-workflow \\
        --step-id phase-0 \\
        --status started
      ```
    MD

    calls = workflow_bash_report_calls(body)
    assert_equal 1, calls.size
    assert_equal "phase-0", calls[0][:step_id]
    assert_equal "my-workflow", calls[0][:workflow_id]
    assert_equal "started", calls[0][:status]
  end

  def test_bash_report_calls_ignores_non_report_commands
    body = <<~MD
      ```bash
      pragma-ai workflow create --workflow-id my-workflow --user-story-id US-1
      pragma-ai workflow gap-report --instance-id X --step-id phase-0
      ```
    MD

    assert_empty workflow_bash_report_calls(body)
  end

  def test_response_contract_present
    assert workflow_response_contract_present?(RESPONSE_CONTRACT_BLOCK)
    refute workflow_response_contract_present?("no marker here")
  end

  def test_approval_prompt_present_requires_all_four_lines
    assert workflow_approval_prompt_present?(RESPONSE_CONTRACT_BLOCK)
    refute workflow_approval_prompt_present?("He completado sin las opciones.")
  end

  def test_execute_now_before_started_true_when_marker_present
    body = STARTED_BASH
    assert workflow_execute_now_before_started?(body)
  end

  def test_execute_now_before_started_false_when_marker_missing
    body = <<~MD
      ```bash
      pragma-ai workflow report \\
        --instance-id "$INSTANCE_ID" \\
        --workflow-id my-workflow \\
        --step-id phase-0-x \\
        --status started
      ```
    MD

    refute workflow_execute_now_before_started?(body)
  end
end

class WorkflowResponseContractValidatorTest < Minitest::Test
  # Integration test: run the real validator against the real KB. If our
  # workflow markdowns comply with the contract, this must return zero
  # findings. This locks the KB against regressions.

  def test_kb_workflows_pass_response_contract_validation
    findings = []
    cleared = []
    validate_workflow_response_contract(findings, cleared)

    contract_findings = findings.select do |f|
      %w[WORKFLOW_RESPONSE_CONTRACT_DRIFT WORKFLOW_RESPONSE_CONTRACT_ERROR].include?(f.id)
    end

    if contract_findings.any?
      messages = contract_findings.map { |f| "#{f.id}: #{f.message}\n#{f.evidence}" }.join("\n---\n")
      flunk("Workflow Response Contract validation failed:\n#{messages}")
    else
      assert_equal ["Workflow Response Contracts and per-phase telemetry calls are complete for every phase"], cleared
    end
  end
end
