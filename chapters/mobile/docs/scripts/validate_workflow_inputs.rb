#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "optparse"
require "yaml"

ROOT = File.expand_path("../../../..", __dir__)
OVERLAY_DIRECTORY = File.join(ROOT, "chapters/mobile/docs/templates/spec-packets")

def parse_options(argv)
  options = {}

  OptionParser.new do |parser|
    parser.banner = "Usage: validate_workflow_inputs.rb --workflow-id ID --inputs-file PATH"
    parser.on("--workflow-id ID", "Workflow identifier declared by its overlay") { |value| options[:workflow_id] = value }
    parser.on("--inputs-file PATH", "YAML or JSON object with only the current invocation inputs") { |value| options[:inputs_file] = value }
    parser.on("--inputs-json JSON", "JSON object with only the current invocation inputs") { |value| options[:inputs_json] = value }
  end.parse!(argv)

  raise OptionParser::MissingArgument, "--workflow-id is required" if options[:workflow_id].to_s.strip.empty?
  if options[:inputs_file].to_s.strip.empty? == options[:inputs_json].to_s.strip.empty?
    raise OptionParser::MissingArgument, "provide exactly one of --inputs-file or --inputs-json"
  end

  options
end

def read_inputs(options)
  if options[:inputs_json]
    JSON.parse(options[:inputs_json])
  else
    source = File.read(options[:inputs_file])
    options[:inputs_file].end_with?(".json") ? JSON.parse(source) : YAML.safe_load(source, aliases: false)
  end
end

def normalize_inputs(inputs)
  raise ArgumentError, "invocation inputs must be a YAML or JSON object" unless inputs.is_a?(Hash)

  inputs.each_with_object({}) do |(key, value), normalized|
    normalized[key.to_s.downcase] = value
  end
end

def present_value?(value)
  case value
  when nil
    false
  when String
    !value.strip.empty?
  when Array
    value.any? { |item| present_value?(item) }
  when Hash
    value.any? { |_key, item| present_value?(item) }
  else
    true
  end
end

def conditional_required_inputs(contract, inputs)
  (contract["conditional_required_inputs"] || []).flat_map do |condition|
    when_values = condition.fetch("when", {})
    matches = when_values.all? do |field, expected|
      inputs[field.to_s.downcase].to_s == expected.to_s
    end
    matches ? Array(condition["required_inputs"]) : []
  end
end

def validation_result(workflow_id, inputs)
  overlay_path = File.join(OVERLAY_DIRECTORY, "#{workflow_id}.overlay.yaml")
  raise ArgumentError, "unknown workflow_id #{workflow_id.inspect}" unless File.file?(overlay_path)

  contract = YAML.safe_load(File.read(overlay_path), aliases: false) || {}
  normalized_inputs = normalize_inputs(inputs)
  required_inputs = Array(contract["required_inputs"]) + conditional_required_inputs(contract, normalized_inputs)
  required_inputs = required_inputs.map(&:to_s).uniq
  missing_inputs = required_inputs.reject { |field| present_value?(normalized_inputs[field.downcase]) }

  {
    "ok" => missing_inputs.empty?,
    "status" => missing_inputs.empty? ? "ready" : "blocked_input",
    "code" => missing_inputs.empty? ? nil : "REQUIRED_INPUT_MISSING",
    "workflow_id" => workflow_id,
    "missing_inputs" => missing_inputs
  }.compact
end

begin
  options = parse_options(ARGV)
  result = validation_result(options[:workflow_id], read_inputs(options))
  puts JSON.generate(result)
  exit(result["ok"] ? 0 : 2)
rescue OptionParser::ParseError, JSON::ParserError, Psych::Exception, ArgumentError, Errno::ENOENT => error
  warn JSON.generate(
    "ok" => false,
    "status" => "blocked_input",
    "code" => "INPUT_PREFLIGHT_INVALID",
    "message" => error.message
  )
  exit 2
end
