#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "minitest/autorun"
require "open3"
require "tmpdir"
require "fileutils"

class MelosWorkspaceTest < Minitest::Test
  SCRIPT = File.expand_path("melos_workspace.rb", __dir__)

  def setup
    @tmp = Dir.mktmpdir("melos-workspace-test")
  end

  def teardown
    FileUtils.remove_entry(@tmp)
  end

  def test_accepts_modern_melos_without_melos_yaml
    write_root_pubspec <<~YAML
      name: workspace
      publish_to: none
      environment:
        sdk: ^3.9.0
      workspace:
        - apps/mobile
      dev_dependencies:
        melos: ^8.0.0
      melos:
        scripts: {}
    YAML
    write_package("apps/mobile", "mobile")

    result, status = resolve("apps/mobile")

    assert status.success?
    assert_equal true, result["ok"]
    assert_equal "root_pubspec", result["config_source"]
    assert_equal "mobile", result["melos_scope"]
  end

  def test_accepts_modern_workspace_glob
    write_root_pubspec <<~YAML
      name: workspace
      environment:
        sdk: ^3.9.0
      workspace:
        - packages/**
      dev_dependencies:
        melos: ^7.0.0
    YAML
    write_package("packages/feature/review", "feature_review")

    result, status = resolve("packages/feature/review")

    assert status.success?
    assert_equal true, result["checks"]["target_package_in_workspace"]
  end

  def test_accepts_legacy_melos_yaml
    write_root_pubspec "name: legacy_root\n"
    File.write(File.join(@tmp, "melos.yaml"), "packages:\n  - packages/**\n")
    write_package("packages/core", "core", resolution: nil)

    result, status = resolve("packages/core")

    assert status.success?
    assert_equal "legacy_yaml", result["config_source"]
    assert_includes result["warnings"], "LEGACY_MELOS_YAML"
  end

  def test_rejects_plain_pub_workspace_without_melos
    write_root_pubspec <<~YAML
      name: workspace
      environment:
        sdk: ^3.9.0
      workspace:
        - packages/core
    YAML
    write_package("packages/core", "core")

    result, status = resolve("packages/core")

    refute status.success?
    assert_equal "CONFIG_MELOS_CONFIG_MISSING", result["code"]
  end

  def test_rejects_modern_package_outside_workspace
    write_root_pubspec <<~YAML
      name: workspace
      environment:
        sdk: ^3.9.0
      workspace:
        - packages/core
      dev_dependencies:
        melos: ^8.0.0
    YAML
    write_package("packages/review", "review")

    result, status = resolve("packages/review")

    refute status.success?
    assert_equal "CONFIG_MELOS_PACKAGE_NOT_IN_WORKSPACE", result["code"]
  end

  def test_rejects_malformed_modern_workspace
    write_root_pubspec <<~YAML
      name: workspace
      environment:
        sdk: ^3.9.0
      workspace: packages/core
      dev_dependencies:
        melos: ^8.0.0
    YAML
    write_package("packages/core", "core")

    result, status = resolve("packages/core")

    refute status.success?
    assert_equal "CONFIG_MELOS_WORKSPACE_INVALID", result["code"]
  end

  def test_accepts_root_package_when_use_root_as_package_is_enabled
    write_root_pubspec <<~YAML
      name: app
      environment:
        sdk: ^3.9.0
      workspace: []
      dev_dependencies:
        melos: ^8.0.0
      melos:
        useRootAsPackage: true
    YAML

    result, status = resolve(".")

    assert status.success?
    assert_equal true, result["root_as_package"]
  end

  private

  def resolve(package_path)
    stdout, stderr, status = Open3.capture3("ruby", SCRIPT, "resolve", "--root", @tmp, "--package-path", package_path)
    assert_empty stderr
    [JSON.parse(stdout), status]
  end

  def write_root_pubspec(contents)
    File.write(File.join(@tmp, "pubspec.yaml"), contents)
  end

  def write_package(relative_path, name, resolution: "workspace")
    path = File.join(@tmp, relative_path)
    FileUtils.mkdir_p(path)
    content = ["name: #{name}"]
    content << "resolution: #{resolution}" if resolution
    File.write(File.join(path, "pubspec.yaml"), "#{content.join("\n")}\n")
  end
end
