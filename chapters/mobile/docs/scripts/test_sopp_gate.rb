#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "fileutils"
require "json"
require "minitest/autorun"
require "open3"
require "tmpdir"
require "yaml"

class SoppGateTest < Minitest::Test
  SCRIPT = File.expand_path("sopp_gate.rb", __dir__)

  def setup
    @tmp = Dir.mktmpdir("sopp-gate-test")
    @packet = File.join(@tmp, "app", ".sopp", "flow_result", "specs", "review")
    @target = File.join(@tmp, "app")
    FileUtils.mkdir_p(File.join(@packet, "schemas"))
    FileUtils.mkdir_p(File.join(@target, "lib", "feature", "review", "domain"))
    FileUtils.mkdir_p(File.join(@packet, "evidence"))
    File.write(File.join(@packet, "schemas", "mobile-spec.schema.yaml"), "type: object\n")
    File.write(File.join(@packet, "schemas", "mobile-context.schema.json"), "{}\n")
    File.write(File.join(@target, "lib", "feature", "review", "domain", "review.dart"), "class Review {}\n")
    write_packet
  end

  def teardown
    FileUtils.remove_entry(@tmp)
  end

  def test_rejects_full_packet_without_layer_review_contract
    spec = YAML.safe_load(File.read(spec_path), aliases: true)
    spec.delete("human_review")
    File.write(spec_path, YAML.dump(spec))

    _out, err, status = run_gate("validate")

    refute status.success?
    assert_includes err, "CONFIG_SPEC_PACKET_INVALID"
    assert_includes err, "human_review"
  end

  def test_rejects_missing_schema_target
    spec = YAML.safe_load(File.read(spec_path), aliases: true)
    spec["schema_ref"] = "schemas/missing-mobile-spec.schema.yaml"
    File.write(spec_path, YAML.dump(spec))

    _out, err, status = run_gate("validate")

    refute status.success?
    assert_includes err, "schema_ref does not exist"
  end

  def test_layer_cannot_advance_without_evidence_and_human_approval
    approve_initial

    _out, err, status = run_gate("open-checkpoint", "--layer", "domain")
    refute status.success?
    assert_includes err, "DOMAIN_EVIDENCE_MISSING"

    File.write(File.join(@packet, "evidence", "domain-checkpoint.md"), "# Domain\n")
    assert_success run_gate("open-checkpoint", "--layer", "domain")

    _out, err, status = run_gate("can-enter", "--phase", "data_layer")
    refute status.success?
    assert_includes err, "DOMAIN_NOT_APPROVED"

    context = read_context
    hash = context.dig("checkpoints", "domain", "artifact_hash")
    challenge = context.dig("checkpoints", "domain", "approval_challenge")
    assert_success run_gate(
      "approve", "--layer", "domain", "--artifact-hash", hash,
      "--approval-id", "human-turn:#{challenge}"
    )
    assert_success run_gate("can-enter", "--phase", "data_layer")

    File.write(File.join(@target, "lib", "feature", "review", "domain", "review.dart"), "class ChangedReview {}\n")
    _out, err, status = run_gate("can-enter", "--phase", "data_layer")
    refute status.success?
    assert_includes err, "artifact hash is stale"
  end

  def test_change_request_requires_proposal_authorization_and_fresh_review
    approve_initial
    File.write(File.join(@packet, "evidence", "domain-checkpoint.md"), "# Domain\n")
    assert_success run_gate("open-checkpoint", "--layer", "domain")
    assert_success run_gate("request-changes", "--layer", "domain", "--message", "Add pagination")

    proposal = File.join(@packet, "revisions", "domain", "001", "proposal.md")
    FileUtils.mkdir_p(File.dirname(proposal))
    File.write(proposal, "# Proposal\n\nAdd PaginationParams.\n")
    assert_success run_gate("propose-adjustment", "--layer", "domain", "--proposal", proposal)
    proposal_hash = read_context.dig("checkpoints", "domain", "proposal_hash")
    challenge = read_context.dig("checkpoints", "domain", "approval_challenge")
    assert_success run_gate(
      "authorize-adjustment", "--layer", "domain", "--proposal-hash", proposal_hash,
      "--approval-id", "human-turn:#{challenge}"
    )

    File.write(File.join(@target, "lib", "feature", "review", "domain", "review.dart"), "class Review { int page = 1; }\n")
    File.write(File.join(@packet, "evidence", "domain-checkpoint.md"), "# Domain revision 1\n")
    assert_success run_gate("open-checkpoint", "--layer", "domain")
    assert_equal "pending", read_context.dig("checkpoints", "domain", "status")
    assert_equal 2, read_context.dig("checkpoints", "domain", "revision")
  end

  private

  def write_packet
    spec = {
      "schema_version" => 1,
      "schema_ref" => "schemas/mobile-spec.schema.yaml",
      "workflow" => "new-feature",
      "spec_level" => "full",
      "execution_mode" => "propose_then_apply",
      "evidence_mode" => "minimal",
      "status" => "proposed",
      "inputs" => { "feature_name" => "review", "description" => "Reviews" },
      "external_access" => {},
      "agent_permissions" => { "feature-builder" => {} },
      "human_review" => {
        "initial_spec_approval" => "required",
        "layer_checkpoints" => "required",
        "stage_checkpoints" => "required"
      },
      "artifact_plan" => {
        "planned" => [{
          "target_id" => "app", "path" => "lib/feature/review/domain/review.dart",
          "group" => "domain", "action" => "create"
        }]
      },
      "target_roots" => { "app" => @target },
      "success_criteria" => [{ "id" => "SC1", "evidence" => ["evidence/domain-checkpoint.md"] }],
      "handoffs" => [{ "phase" => "domain_layer", "read_sections" => ["artifact_plan"] }]
    }
    File.write(spec_path, YAML.dump(spec))
    context = {
      "schema_version" => 1,
      "schema_ref" => "schemas/mobile-context.schema.json",
      "run_id" => "review-test",
      "workflow" => "new-feature",
      "spec_level" => "full",
      "workflow_controller" => "feature-builder",
      "packet_owner_target_id" => "app",
      "packet_root" => @packet,
      "status" => "pending_human_review",
      "current_phase" => "spec_review",
      "checkpoints" => {
        "initial_spec" => {
          "required" => true, "phase" => "spec_review", "status" => "pending",
          "decision_ref" => "review.md"
        }
      },
      "completed_phases" => [], "phase_results" => {}, "artifacts" => {},
      "pending_human_review" => { "kind" => "initial_spec_approval", "review_ref" => "review.md" }
    }
    File.write(context_path, JSON.pretty_generate(context) + "\n")
    File.write(File.join(@packet, "review.md"), "# Review\n")
  end

  def approve_initial
    assert_success run_gate("open-initial")
    checkpoint = read_context.dig("checkpoints", "initial_spec")
    assert_success run_gate(
      "approve-initial", "--spec-hash", checkpoint["artifact_hash"],
      "--approval-id", "human-turn:#{checkpoint['approval_challenge']}"
    )
  end

  def run_gate(*args)
    Open3.capture3("ruby", SCRIPT, args.first, "--packet", @packet, *args.drop(1))
  end

  def assert_success(result)
    out, err, status = result
    assert status.success?, "expected success; stdout=#{out.inspect}; stderr=#{err.inspect}"
  end

  def read_context
    JSON.parse(File.read(context_path))
  end

  def spec_path
    File.join(@packet, "spec.yaml")
  end

  def context_path
    File.join(@packet, "context.json")
  end
end
