#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "minitest/autorun"
require "open3"
require "tmpdir"

SCRIPTS_DIRECTORY = File.expand_path(__dir__)
VALIDATOR = File.join(SCRIPTS_DIRECTORY, "validate_mobile_kb.rb")

class ValidateMobileKbExportTest < Minitest::Test
  def test_validates_each_exported_platform_kb_without_source_paths
    Dir.mktmpdir("mobile-kb-export") do |root|
      %w[.claude .github .kiro].each do |platform_root|
        export_root = File.join(root, platform_root)
        scripts_root = File.join(export_root, "docs", "scripts")
        overlays_root = File.join(export_root, "docs", "templates", "spec-packets")
        FileUtils.mkdir_p(scripts_root)
        FileUtils.mkdir_p(overlays_root)

        %w[validate_mobile_kb.rb validate_workflow_inputs.rb sopp_gate.rb melos_workspace.rb].each do |script|
          FileUtils.cp(File.join(SCRIPTS_DIRECTORY, script), scripts_root)
        end
        FileUtils.cp(
          File.expand_path("../templates/spec-packets/new-feature.overlay.yaml", __dir__),
          overlays_root
        )

        stdout, stderr, status = Open3.capture3(
          "ruby", File.join(scripts_root, "validate_mobile_kb.rb")
        )

        assert_predicate status, :success?, stderr
        assert_includes stdout, "Mobile KB validation OK"
        assert_includes stdout, "Exported #{platform_root} KB"
      end
    end
  end
end
