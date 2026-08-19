#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "optparse"
require "pathname"
require "yaml"

# Resolves a Melos workspace without network access or a Melos installation.
#
# Supports both configurations:
# - legacy Melos 6: <root>/melos.yaml
# - modern Melos 7+: <root>/pubspec.yaml with a Dart pub workspace and a Melos
#   dependency or `melos:` section.
#
# The command verifies the target package rather than treating a filename as
# sufficient proof. It is intended for preflight checks in the exported KB.
class MelosWorkspaceResolver
  def initialize(root:, package_path:)
    @root_input = root.to_s
    @root = File.expand_path(@root_input)
    @package_path_input = package_path
    @warnings = []
    @checks = {}
  end

  def resolve
    return failure("CONFIG_MELOS_ROOT_MISSING", "Workspace root is required") if @root_input.empty?
    return failure("CONFIG_MELOS_ROOT_MISSING", "Workspace root does not exist") unless Dir.exist?(@root)

    package_root = resolve_package_root
    return package_root if package_root.is_a?(Hash) && package_root["ok"] == false

    root_pubspec_path = File.join(@root, "pubspec.yaml")
    root_pubspec = parse_yaml(root_pubspec_path, "CONFIG_MELOS_ROOT_PUBSPEC_INVALID")
    return root_pubspec if root_pubspec.is_a?(Hash) && root_pubspec["ok"] == false

    legacy_path = File.join(@root, "melos.yaml")
    legacy_config = if File.file?(legacy_path)
                      parse_yaml(legacy_path, "CONFIG_MELOS_LEGACY_CONFIG_INVALID")
                    end
    return legacy_config if legacy_config.is_a?(Hash) && legacy_config["ok"] == false

    modern = modern_workspace?(root_pubspec, package_root)
    legacy = legacy_config.is_a?(Hash)

    if modern
      @warnings << "LEGACY_MELOS_YAML_IGNORED" if legacy
      validate_modern(root_pubspec, package_root, root_pubspec_path)
    elsif legacy
      validate_legacy(legacy_config, package_root, legacy_path, root_pubspec_path)
    else
      failure(
        "CONFIG_MELOS_CONFIG_MISSING",
        "Expected legacy melos.yaml or a modern root pubspec.yaml with workspace and Melos configuration"
      )
    end
  end

  private

  def resolve_package_root
    raw_path = @package_path_input.to_s
    return failure("CONFIG_MELOS_PACKAGE_PATH_MISSING", "package_path is required") if raw_path.empty?

    candidate = if Pathname.new(raw_path).absolute?
                  File.expand_path(raw_path)
                else
                  File.expand_path(raw_path, @root)
                end
    root_prefix = @root.end_with?(File::SEPARATOR) ? @root : "#{@root}#{File::SEPARATOR}"
    unless candidate == @root || candidate.start_with?(root_prefix)
      return failure("CONFIG_MELOS_PACKAGE_OUTSIDE_ROOT", "package_path must resolve inside the workspace root")
    end
    return failure("CONFIG_MELOS_PACKAGE_MISSING", "Target package directory does not exist") unless Dir.exist?(candidate)

    package_pubspec_path = File.join(candidate, "pubspec.yaml")
    return failure("CONFIG_MELOS_PACKAGE_PUBSPEC_MISSING", "Target package is missing pubspec.yaml") unless File.file?(package_pubspec_path)

    package_pubspec = parse_yaml(package_pubspec_path, "CONFIG_MELOS_PACKAGE_PUBSPEC_INVALID")
    return package_pubspec if package_pubspec.is_a?(Hash) && package_pubspec["ok"] == false

    @checks["target_package_exists"] = true
    @checks["target_package_pubspec_exists"] = true
    {
      root: candidate,
      relative_path: relative_path(candidate),
      pubspec_path: package_pubspec_path,
      pubspec: package_pubspec
    }
  end

  def modern_workspace?(root_pubspec, package_root)
    return false unless root_pubspec.is_a?(Hash)

    workspace_declared = root_pubspec.key?("workspace")
    root_as_package = package_root[:relative_path] == "." && root_pubspec.dig("melos", "useRootAsPackage") == true
    melos_declared = root_pubspec["melos"].is_a?(Hash) ||
                     root_pubspec.dig("dev_dependencies", "melos") ||
                     root_pubspec.dig("dependencies", "melos")
    !!melos_declared && (workspace_declared || root_as_package)
  end

  def validate_modern(root_pubspec, package_root, root_pubspec_path)
    workspace = root_pubspec["workspace"]
    root_as_package = package_root[:relative_path] == "." && root_pubspec.dig("melos", "useRootAsPackage") == true

    unless workspace.is_a?(Array)
      code = root_pubspec.key?("workspace") ? "CONFIG_MELOS_WORKSPACE_INVALID" : "CONFIG_MELOS_WORKSPACE_MISSING"
      return failure(code, "Modern Melos requires a root workspace list")
    end
    unless workspace.all? { |entry| entry.is_a?(String) && !entry.empty? }
      return failure("CONFIG_MELOS_WORKSPACE_INVALID", "workspace entries must be non-empty strings")
    end

    dependency_declared = root_pubspec.dig("dev_dependencies", "melos") || root_pubspec.dig("dependencies", "melos")
    @warnings << "MELOS_VERSION_UNPINNED" unless dependency_declared

    member = root_as_package || workspace.any? do |entry|
      workspace_entry_matches?(entry, package_root[:root])
    end
    unless member
      return failure("CONFIG_MELOS_PACKAGE_NOT_IN_WORKSPACE", "Target package is not included by root pubspec.yaml workspace")
    end

    unless root_as_package || package_root[:pubspec]["resolution"] == "workspace"
      return failure(
        "CONFIG_MELOS_PACKAGE_RESOLUTION_MISSING",
        "Modern Melos packages must declare resolution: workspace"
      )
    end

    @checks["root_pubspec_exists"] = true
    @checks["modern_melos_config_detected"] = true
    @checks["target_package_in_workspace"] = true
    @checks["target_package_resolution_workspace"] = root_as_package || package_root[:pubspec]["resolution"] == "workspace"
    success(
      config_source: "root_pubspec",
      config_path: root_pubspec_path,
      package_root: package_root,
      workspace_entries: workspace,
      root_as_package: root_as_package
    )
  end

  def validate_legacy(legacy_config, package_root, legacy_path, root_pubspec_path)
    packages = legacy_config["packages"]
    unless packages.is_a?(Array) && packages.all? { |entry| entry.is_a?(String) && !entry.empty? }
      return failure("CONFIG_MELOS_LEGACY_PACKAGES_INVALID", "Legacy melos.yaml must declare a packages list")
    end
    unless packages.any? { |entry| workspace_entry_matches?(entry, package_root[:root]) }
      return failure("CONFIG_MELOS_PACKAGE_NOT_IN_WORKSPACE", "Target package is not included by legacy melos.yaml packages")
    end

    @warnings << "LEGACY_MELOS_YAML" 
    @warnings << "ROOT_PUBSPEC_MISSING" unless File.file?(root_pubspec_path)
    @checks["legacy_melos_config_detected"] = true
    @checks["target_package_in_workspace"] = true
    success(
      config_source: "legacy_yaml",
      config_path: legacy_path,
      package_root: package_root,
      workspace_entries: packages,
      root_as_package: false
    )
  end

  def workspace_entry_matches?(entry, package_root)
    normalized_entry = entry.tr("\\", "/").sub(%r{/+$}, "")
    return false if normalized_entry.empty?

    entry_path = File.expand_path(normalized_entry, @root)
    return true if entry_path == package_root

    return false unless normalized_entry.match?(/[\*\?\[]/)

    Dir.glob(File.join(@root, normalized_entry, "pubspec.yaml"), File::FNM_EXTGLOB).any? do |pubspec_path|
      File.dirname(File.expand_path(pubspec_path)) == package_root
    end
  end

  def parse_yaml(path, error_code)
    return nil unless File.file?(path)

    value = YAML.safe_load(File.read(path), aliases: true)
    return failure(error_code, "YAML root must be a mapping: #{relative_path(path)}") unless value.is_a?(Hash)

    value
  rescue Psych::SyntaxError => error
    failure(error_code, "Unable to parse #{relative_path(path)}: #{error.message.lines.first.strip}")
  end

  def success(config_source:, config_path:, package_root:, workspace_entries:, root_as_package:)
    {
      "ok" => true,
      "repo_mode" => "monorepo_melos",
      "melos_root" => @root,
      "config_source" => config_source,
      "config_path" => config_path,
      "package_path" => package_root[:relative_path],
      "package_pubspec_path" => package_root[:pubspec_path],
      "package_name" => package_root[:pubspec]["name"],
      "melos_scope" => package_root[:pubspec]["name"],
      "workspace_entries" => workspace_entries,
      "root_as_package" => root_as_package,
      "checks" => @checks,
      "warnings" => @warnings
    }
  end

  def failure(code, message)
    {
      "ok" => false,
      "code" => code,
      "message" => message,
      "melos_root" => @root,
      "checks" => @checks,
      "warnings" => @warnings
    }
  end

  def relative_path(path)
    Pathname.new(path).relative_path_from(Pathname.new(@root)).to_s.then { |value| value.empty? ? "." : value }
  rescue ArgumentError
    path
  end
end

options = {}
OptionParser.new do |parser|
  parser.banner = "Usage: melos_workspace.rb resolve --root PATH --package-path PATH"
  parser.on("--root PATH", "Melos workspace root") { |value| options[:root] = value }
  parser.on("--package-path PATH", "Target package path relative to root") { |value| options[:package_path] = value }
  parser.on("-h", "--help", "Show help") do
    puts parser
    exit 0
  end
end.parse!

unless ARGV == ["resolve"] || ARGV.empty?
  warn JSON.generate("ok" => false, "code" => "CONFIG_MELOS_COMMAND_INVALID", "message" => "Only resolve is supported")
  exit 64
end

result = MelosWorkspaceResolver.new(root: options[:root].to_s, package_path: options[:package_path].to_s).resolve
puts JSON.pretty_generate(result)
exit(result["ok"] ? 0 : 2)
