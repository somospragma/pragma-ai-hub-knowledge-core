#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "minitest/autorun"
require "open3"

SCRIPT = File.expand_path("validate_workflow_inputs.rb", __dir__)

class ValidateWorkflowInputsTest < Minitest::Test
  def run_validator(workflow_id, inputs)
    stdout, stderr, status = Open3.capture3(
      "ruby", SCRIPT,
      "--workflow-id", workflow_id,
      "--inputs-json", JSON.generate(inputs)
    )
    [JSON.parse(stdout.empty? ? stderr : stdout), status]
  end

  def test_accepts_all_non_blank_required_inputs
    result, status = run_validator(
      "new-feature",
      "hu_id" => "US-123",
      "feature_name" => "catalog",
      "description" => "Browse the product catalog"
    )

    assert_predicate status, :success?
    assert_equal true, result["ok"]
    assert_empty result["missing_inputs"]
  end

  def test_rejects_missing_and_blank_required_inputs
    result, status = run_validator(
      "new-feature",
      "hu_id" => "   ",
      "feature_name" => "catalog"
    )

    assert_equal 2, status.exitstatus
    assert_equal "blocked_input", result["status"]
    assert_equal %w[hu_id description], result["missing_inputs"]
  end

  def test_requires_ddd_inputs_only_when_ddd_mode_is_selected
    result, status = run_validator(
      "new-feature",
      "hu_id" => "US-123",
      "feature_name" => "checkout",
      "description" => "Complete checkout",
      "domain_modeling" => "ddd",
      "business_rules" => "   ",
      "domain_boundaries" => "Checkout owns orders"
    )

    assert_equal 2, status.exitstatus
    assert_equal %w[business_rules server_authority], result["missing_inputs"]
  end

  def test_accepts_non_empty_nested_input
    result, status = run_validator(
      "fix-pr-comments",
      "hu_id" => "US-123",
      "pr_comments_source" => { "kind" => "pr_url" }
    )

    assert_predicate status, :success?
    assert_equal true, result["ok"]
  end

  def test_normalizes_non_hu_bootstrap_input_key_case
    result, status = run_validator(
      "bootstrap-workspace",
      "hu_id" => "US-123",
      "WORKSPACE_ROOT" => "/workspace"
    )

    assert_predicate status, :success?
    assert_equal true, result["ok"]
  end
end
