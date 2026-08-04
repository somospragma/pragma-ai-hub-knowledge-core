#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "fileutils"
require "json"
require "optparse"
require "securerandom"
require "time"
require "yaml"

module SoppGate
  LAYERS = %w[domain data presentation].freeze
  PREVIOUS_LAYER = { "domain" => "initial_spec", "data" => "domain", "presentation" => "data" }.freeze
  NEXT_PHASE = { "domain" => "data_layer", "data" => "presentation_layer", "presentation" => "wiring" }.freeze
  EVIDENCE = LAYERS.to_h { |layer| [layer, "evidence/#{layer}-checkpoint.md"] }.freeze
  STATUS_VALUES = %w[pending changes_requested adjustment_proposed revision_authorized approved stale].freeze

  class GateError < StandardError
    attr_reader :code

    def initialize(code, message)
      @code = code
      super(message)
    end
  end

  class Packet
    attr_reader :root, :spec, :context

    def initialize(root)
      @root = File.expand_path(root)
      @spec_path = File.join(@root, "spec.yaml")
      @context_path = File.join(@root, "context.json")
      require_file!(@spec_path, "SPEC_MISSING")
      require_file!(@context_path, "CONTEXT_MISSING")
      @spec = YAML.safe_load(File.read(@spec_path), aliases: true)
      @context = JSON.parse(File.read(@context_path))
    rescue Psych::SyntaxError, JSON::ParserError => e
      raise GateError.new("PACKET_PARSE_ERROR", e.message)
    end

    def validate!
      errors = []
      %w[schema_version workflow spec_level execution_mode evidence_mode status inputs external_access agent_permissions human_review artifact_plan success_criteria handoffs].each do |field|
        errors << "spec.yaml missing #{field}" unless spec.key?(field)
      end
      if spec["spec_level"] == "full"
        %w[initial_spec_approval layer_checkpoints stage_checkpoints].each do |field|
          errors << "human_review.#{field} must be required" unless spec.dig("human_review", field) == "required"
        end
      end
      validate_schema_ref(errors, @spec_path, spec["schema_ref"], "mobile-spec.schema.yaml")
      validate_schema_ref(errors, @context_path, context["schema_ref"], "mobile-context.schema.json")
      errors << "context.json checkpoints must be an object" unless context["checkpoints"].is_a?(Hash)
      errors << "context.json phase_results must be an object" unless context["phase_results"].is_a?(Hash)
      errors << "context.json artifacts must be an object" unless context["artifacts"].is_a?(Hash)
      validate_approved_checkpoints(errors)
      raise GateError.new("CONFIG_SPEC_PACKET_INVALID", errors.join("; ")) unless errors.empty?

      true
    end

    def open_checkpoint!(layer)
      validate_layer!(layer)
      validate!
      previous = checkpoint(PREVIOUS_LAYER.fetch(layer))
      unless previous && previous["status"] == "approved"
        raise GateError.new("PREVIOUS_CHECKPOINT_NOT_APPROVED", "#{PREVIOUS_LAYER.fetch(layer)} must be approved before #{layer}")
      end
      evidence_ref = EVIDENCE.fetch(layer)
      require_file!(File.join(root, evidence_ref), "#{layer.upcase}_EVIDENCE_MISSING")
      digest = artifact_digest(layer)
      context["checkpoints"][layer] = {
        "required" => true,
        "phase" => "#{layer}_layer",
        "status" => "pending",
        "decision_ref" => evidence_ref,
        "artifact_hash" => digest,
        "approval_challenge" => SecureRandom.hex(4),
        "revision" => next_revision(layer),
        "generated_at" => now
      }
      context["status"] = "pending_human_review"
      context["current_phase"] = "#{layer}_checkpoint"
      context["pending_human_review"] = { "kind" => "#{layer}_approval", "review_ref" => evidence_ref }
      context["completed_phases"] ||= []
      context["completed_phases"] << "#{layer}_layer" unless context["completed_phases"].include?("#{layer}_layer")
      context["phase_results"] ||= {}
      context["phase_results"]["#{layer}_layer"] = {
        "status" => "completed", "summary" => "#{layer.capitalize} generated; awaiting human approval.",
        "refs" => [evidence_ref]
      }
      append_event("checkpoint_opened", layer, "artifact_hash" => digest, "evidence_ref" => evidence_ref)
      save!
    end

    def open_initial!
      validate!
      cp = checkpoint("initial_spec")
      unless cp && cp["status"] == "pending"
        raise GateError.new("INITIAL_SPEC_NOT_PENDING", "initial_spec must be pending")
      end
      require_file!(File.join(root, cp["decision_ref"]), "INITIAL_REVIEW_MISSING")
      cp["artifact_hash"] = "sha256:#{Digest::SHA256.file(@spec_path).hexdigest}"
      cp["approval_challenge"] = SecureRandom.hex(4)
      context["status"] = "pending_human_review"
      context["current_phase"] = "spec_review"
      context["pending_human_review"] = { "kind" => "initial_spec_approval", "review_ref" => cp["decision_ref"] }
      append_event("initial_checkpoint_opened", "initial_spec", "artifact_hash" => cp["artifact_hash"])
      save!
    end

    def request_changes!(layer, message)
      validate_layer!(layer)
      require_status!(layer, "pending", "CHECKPOINT_NOT_PENDING")
      raise GateError.new("CHANGE_REQUEST_EMPTY", "A human change request is required") if message.to_s.strip.empty?

      revision = checkpoint(layer)["revision"] || 1
      ref = "revisions/#{layer}/#{format('%03d', revision)}/request.json"
      write_json(ref, {
        "event" => "changes_requested", "layer" => layer, "revision" => revision,
        "requested_at" => now, "requested_by" => "human", "request" => message,
        "reviewed_hash" => checkpoint(layer)["artifact_hash"]
      })
      checkpoint(layer)["status"] = "changes_requested"
      checkpoint(layer)["change_request_ref"] = ref
      context["pending_human_review"] = nil
      append_event("changes_requested", layer, "request_ref" => ref)
      save!
    end

    def propose_adjustment!(layer, proposal_path)
      validate_layer!(layer)
      require_status!(layer, "changes_requested", "CHANGE_REQUEST_REQUIRED")
      absolute = File.expand_path(proposal_path)
      require_file!(absolute, "ADJUSTMENT_PROPOSAL_MISSING")
      unless absolute.start_with?(root + File::SEPARATOR)
        raise GateError.new("PROPOSAL_OUTSIDE_PACKET", "Adjustment proposal must live inside the packet")
      end
      proposal_ref = absolute.delete_prefix(root + File::SEPARATOR)
      proposal_hash = "sha256:#{Digest::SHA256.file(absolute).hexdigest}"
      checkpoint(layer)["status"] = "adjustment_proposed"
      checkpoint(layer)["proposal_ref"] = proposal_ref
      checkpoint(layer)["proposal_hash"] = proposal_hash
      checkpoint(layer)["approval_challenge"] = SecureRandom.hex(4)
      context["status"] = "pending_human_review"
      context["pending_human_review"] = { "kind" => "#{layer}_adjustment_authorization", "review_ref" => proposal_ref }
      append_event("adjustment_proposed", layer, "proposal_ref" => proposal_ref, "proposal_hash" => proposal_hash)
      save!
    end

    def authorize_adjustment!(layer, proposal_hash, approval_id)
      validate_layer!(layer)
      require_status!(layer, "adjustment_proposed", "ADJUSTMENT_PROPOSAL_REQUIRED")
      unless checkpoint(layer)["proposal_hash"] == proposal_hash
        raise GateError.new("PROPOSAL_HASH_MISMATCH", "Authorization does not match the proposed adjustment")
      end
      require_human_approval_id!(approval_id, checkpoint(layer))
      ref = approval_ref(layer, "revision-authorization")
      write_json(ref, approval_payload(layer, approval_id).merge(
        "event" => "adjustment_authorized", "proposal_hash" => proposal_hash
      ))
      checkpoint(layer)["status"] = "revision_authorized"
      checkpoint(layer)["authorization_ref"] = ref
      context["status"] = "approved_for_execution"
      context["current_phase"] = "#{layer}_revision"
      context["pending_human_review"] = nil
      invalidate_from!(layer, include_current: false)
      append_event("adjustment_authorized", layer, "approval_ref" => ref, "proposal_hash" => proposal_hash)
      save!
    end

    def approve!(layer, artifact_hash, approval_id)
      validate_layer!(layer)
      require_status!(layer, "pending", "CHECKPOINT_NOT_PENDING")
      require_human_approval_id!(approval_id, checkpoint(layer))
      actual = artifact_digest(layer)
      expected = checkpoint(layer)["artifact_hash"]
      unless artifact_hash == expected && actual == expected
        raise GateError.new("ARTIFACT_HASH_MISMATCH", "Artifacts changed after review; reopen the #{layer} checkpoint")
      end
      ref = approval_ref(layer, "approval")
      write_json(ref, approval_payload(layer, approval_id).merge(
        "event" => "layer_approved", "reviewed_hash" => artifact_hash,
        "evidence_ref" => checkpoint(layer)["decision_ref"]
      ))
      checkpoint(layer)["status"] = "approved"
      checkpoint(layer)["approval_ref"] = ref
      checkpoint(layer)["approved_at"] = now
      context["status"] = "approved_for_execution"
      context["current_phase"] = NEXT_PHASE.fetch(layer)
      context["pending_human_review"] = nil
      append_event("layer_approved", layer, "approval_ref" => ref, "reviewed_hash" => artifact_hash)
      save!
    end

    def approve_initial!(spec_hash, approval_id)
      validate!
      cp = checkpoint("initial_spec")
      unless cp && cp["status"] == "pending"
        raise GateError.new("INITIAL_SPEC_NOT_PENDING", "initial_spec must be pending")
      end
      require_human_approval_id!(approval_id, cp)
      actual = "sha256:#{Digest::SHA256.file(@spec_path).hexdigest}"
      unless spec_hash == actual
        raise GateError.new("SPEC_HASH_MISMATCH", "The approved spec hash does not match spec.yaml")
      end
      ref = "approvals/initial-spec.json"
      write_json(ref, {
        "event" => "initial_spec_approved", "approved_by" => "human",
        "approval_id" => approval_id, "approved_at" => now,
        "reviewed_hash" => actual, "decision_ref" => cp["decision_ref"]
      })
      cp["status"] = "approved"
      cp["approval_ref"] = ref
      cp["approved_at"] = now
      cp["artifact_hash"] = actual
      context["status"] = "approved_for_execution"
      context["current_phase"] = "domain_layer"
      context["pending_human_review"] = nil
      context["completed_phases"] ||= []
      context["completed_phases"] << "spec_review" unless context["completed_phases"].include?("spec_review")
      append_event("initial_spec_approved", "initial_spec", "approval_ref" => ref, "reviewed_hash" => actual)
      save!
    end

    def assert_can_enter!(phase)
      validate!
      required = case phase
                 when "domain_layer" then "initial_spec"
                 when "data_layer" then "domain"
                 when "presentation_layer" then "data"
                 when "wiring" then "presentation"
                 else raise GateError.new("UNKNOWN_PHASE", phase)
                 end
      cp = checkpoint(required)
      unless cp && cp["status"] == "approved"
        raise GateError.new("#{required.upcase}_NOT_APPROVED", "Cannot enter #{phase}; #{required} is not approved")
      end
      true
    end

    private

    def checkpoint(layer)
      context.fetch("checkpoints", {})[layer]
    end

    def now
      Time.now.iso8601
    end

    def validate_layer!(layer)
      raise GateError.new("UNKNOWN_LAYER", layer.to_s) unless LAYERS.include?(layer)
    end

    def require_status!(layer, expected, code)
      actual = checkpoint(layer)&.dig("status")
      raise GateError.new(code, "#{layer} status is #{actual.inspect}; expected #{expected}") unless actual == expected
    end

    def require_human_approval_id!(approval_id, cp)
      challenge = cp["approval_challenge"]
      expected = "human-turn:#{challenge}"
      return if !challenge.to_s.empty? && approval_id == expected

      raise GateError.new("HUMAN_APPROVAL_ID_REQUIRED", "A later human turn must repeat the checkpoint approval challenge")
    end

    def validate_schema_ref(errors, source_path, ref, expected_name)
      if ref.to_s.empty?
        errors << "#{File.basename(source_path)} missing schema_ref"
        return
      end
      errors << "#{File.basename(source_path)} schema_ref must end with #{expected_name}" unless File.basename(ref) == expected_name
      resolved = File.expand_path(ref, File.dirname(source_path))
      errors << "#{File.basename(source_path)} schema_ref does not exist: #{ref}" unless File.file?(resolved)
    end

    def validate_approved_checkpoints(errors)
      context.fetch("checkpoints", {}).each do |name, cp|
        next unless cp.is_a?(Hash) && cp["status"] == "approved"
        %w[decision_ref approval_ref approved_at].each do |field|
          errors << "approved checkpoint #{name} missing #{field}" if cp[field].to_s.empty?
        end
        errors << "approved checkpoint #{name} missing artifact_hash" if cp["artifact_hash"].to_s.empty?
        approval = cp["approval_ref"] && File.join(root, cp["approval_ref"])
        errors << "approved checkpoint #{name} approval_ref does not exist" unless approval && File.file?(approval)
        if approval && File.file?(approval)
          record = JSON.parse(File.read(approval))
          expected_approval_id = "human-turn:#{cp['approval_challenge']}"
          unless record["approved_by"] == "human" && record["approval_id"] == expected_approval_id
            errors << "approved checkpoint #{name} has no human approval identity"
          end
        end
        begin
          actual_hash = if name == "initial_spec"
                          "sha256:#{Digest::SHA256.file(@spec_path).hexdigest}"
                        elsif LAYERS.include?(name)
                          artifact_digest(name)
                        end
          errors << "approved checkpoint #{name} artifact hash is stale" if actual_hash && actual_hash != cp["artifact_hash"]
        rescue GateError => e
          errors << "approved checkpoint #{name} cannot be verified: #{e.code} #{e.message}"
        end
      end
    rescue JSON::ParserError => e
      errors << "approval record is invalid JSON: #{e.message}"
    end

    def artifact_digest(layer)
      planned = spec.dig("artifact_plan", "planned") || []
      entries = planned.select { |entry| entry["group"] == layer }
      raise GateError.new("ARTIFACT_PLAN_EMPTY", "No artifact_plan entries for #{layer}") if entries.empty?

      digest = Digest::SHA256.new
      entries.sort_by { |entry| [entry["target_id"].to_s, entry["path"].to_s] }.each do |entry|
        digest << entry["target_id"].to_s << "\0" << entry["path"].to_s << "\0"
        resolved = resolve_artifact(entry)
        raise GateError.new("PLANNED_ARTIFACT_MISSING", "#{entry['target_id']}:#{entry['path']}") unless File.file?(resolved)
        digest << Digest::SHA256.file(resolved).hexdigest << "\0"
      end
      "sha256:#{digest.hexdigest}"
    end

    def resolve_artifact(entry)
      roots = spec["target_roots"] || {}
      target_root = roots[entry["target_id"]]
      return File.expand_path(entry["path"], target_root) if target_root

      config = find_project_config
      if config
        project = YAML.safe_load(File.read(config), aliases: true)
        configured_root = project.dig("targets", "registry", entry["target_id"], "root")
        return File.expand_path(entry["path"], configured_root) if configured_root
      end

      raise GateError.new("TARGET_ROOT_UNRESOLVED", "Cannot resolve target #{entry['target_id']} from spec.target_roots or .sopp/config/project.config.yaml")
    end

    def find_project_config
      current = root
      loop do
        candidate = File.join(current, ".sopp", "config", "project.config.yaml")
        return candidate if File.file?(candidate)
        parent = File.dirname(current)
        return nil if parent == current
        current = parent
      end
    end

    def next_revision(layer)
      current = checkpoint(layer)&.dig("revision").to_i
      [current + 1, 1].max
    end

    def invalidate_from!(layer, include_current: true)
      start = LAYERS.index(layer) + (include_current ? 0 : 1)
      LAYERS.drop(start).each do |candidate|
        next unless checkpoint(candidate)
        checkpoint(candidate)["status"] = "stale"
        checkpoint(candidate).delete("approval_ref")
        checkpoint(candidate).delete("approved_at")
      end
    end

    def approval_ref(layer, kind)
      revision = checkpoint(layer)["revision"] || 1
      "approvals/#{layer}-#{format('%03d', revision)}-#{kind}.json"
    end

    def approval_payload(layer, approval_id)
      { "layer" => layer, "revision" => checkpoint(layer)["revision"], "approved_by" => "human", "approval_id" => approval_id, "approved_at" => now }
    end

    def append_event(event, layer, data = {})
      ref = "events.jsonl"
      path = File.join(root, ref)
      FileUtils.mkdir_p(File.dirname(path))
      File.open(path, "a") { |file| file.puts(JSON.generate({ "event" => event, "layer" => layer, "at" => now }.merge(data))) }
    end

    def write_json(ref, payload)
      path = File.join(root, ref)
      FileUtils.mkdir_p(File.dirname(path))
      File.write(path, JSON.pretty_generate(payload) + "\n")
    end

    def save!
      File.write(@context_path, JSON.pretty_generate(context) + "\n")
    end

    def require_file!(path, code)
      raise GateError.new(code, path) unless File.file?(path)
    end
  end
end

options = {}
parser = OptionParser.new do |opts|
  opts.banner = "Usage: sopp_gate.rb COMMAND --packet PATH [options]"
  opts.on("--packet PATH") { |value| options[:packet] = value }
  opts.on("--layer LAYER") { |value| options[:layer] = value }
  opts.on("--phase PHASE") { |value| options[:phase] = value }
  opts.on("--message MESSAGE") { |value| options[:message] = value }
  opts.on("--proposal PATH") { |value| options[:proposal] = value }
  opts.on("--proposal-hash HASH") { |value| options[:proposal_hash] = value }
  opts.on("--artifact-hash HASH") { |value| options[:artifact_hash] = value }
  opts.on("--spec-hash HASH") { |value| options[:spec_hash] = value }
  opts.on("--approval-id ID") { |value| options[:approval_id] = value }
end

command = ARGV.shift
parser.parse!(ARGV)
abort(parser.to_s) unless command && options[:packet]

begin
  packet = SoppGate::Packet.new(options[:packet])
  case command
  when "validate" then packet.validate!
  when "open-initial" then packet.open_initial!
  when "open-checkpoint" then packet.open_checkpoint!(options[:layer])
  when "request-changes" then packet.request_changes!(options[:layer], options[:message])
  when "propose-adjustment" then packet.propose_adjustment!(options[:layer], options[:proposal])
  when "authorize-adjustment" then packet.authorize_adjustment!(options[:layer], options[:proposal_hash], options[:approval_id])
  when "approve" then packet.approve!(options[:layer], options[:artifact_hash], options[:approval_id])
  when "approve-initial" then packet.approve_initial!(options[:spec_hash], options[:approval_id])
  when "can-enter" then packet.assert_can_enter!(options[:phase])
  else raise SoppGate::GateError.new("UNKNOWN_COMMAND", command)
  end
  selected = options[:layer] ? packet.context.dig("checkpoints", options[:layer]) : packet.context.dig("checkpoints", "initial_spec")
  puts JSON.generate(status: "ok", command: command, checkpoint: selected)
rescue SoppGate::GateError => e
  warn JSON.generate(status: "blocked", code: e.code, message: e.message)
  exit 2
end
