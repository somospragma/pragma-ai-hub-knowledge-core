#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variable to store the skills directory
SKILLS_DIR=""
NO_LLM=false

# Function to display help
show_help() {
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║       Skill Inspector Batch Processor - Help Documentation     ║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BLUE}DESCRIPTION:${NC}"
  echo "  Sequentially executes 'skillspector scan' for each skill in a specific"
  echo "  directory, generating reports in markdown format."
  echo ""
  echo -e "${BLUE}USAGE:${NC}"
  echo "  ./scan_skills.sh [OPTIONS]"
  echo ""
  echo -e "${BLUE}OPTIONS:${NC}"
  echo -e "  ${GREEN}--path <path>${NC}      ${GREEN}(REQUIRED)${NC} Path to the directory containing skills"
  echo ""
  echo -e "  ${GREEN}--no-llm${NC}           Disables LLM analysis in skillspector"
  echo ""
  echo -e "  ${GREEN}--help${NC}              Shows this help information"
  echo ""
  echo -e "${BLUE}EXAMPLES:${NC}"
  echo "  # Run with a path"
  echo "  ./scan_skills.sh --path ./chapters/backend/skills/java-spring"
  echo ""
  echo "  # Run without LLM"
  echo "  ./scan_skills.sh --path ./chapters/mobile/skills/flutter --no-llm"
  echo ""
  echo "  # View this help"
  echo "  ./scan_skills.sh --help"
  echo ""
  echo -e "${BLUE}REQUIREMENTS:${NC}"
  echo "  - skillspector must be installed"
  echo -e "    Install from: ${YELLOW}https://github.com/NVIDIA/SkillSpector${NC}"
  echo ""
  echo -e "${BLUE}OUTPUT:${NC}"
  echo "  Reports will be generated in:"
  echo "  <skill_dir>/evals/<skill_name>.md"
  echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --path)
      SKILLS_DIR="$2"
      shift 2
      ;;
    --no-llm)
      NO_LLM=true
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown parameter: $1${NC}"
      echo -e "${YELLOW}Use --help to see available options${NC}"
      exit 1
      ;;
  esac
done

# Validate that --path is provided
if [ -z "$SKILLS_DIR" ]; then
  echo ""
  print_error "The --path parameter is required"
  echo ""
  echo -e "${YELLOW}Use --help to see available options${NC}"
  echo ""
  exit 1
fi

# Function to print section header
print_header() {
  echo ""
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  $1"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

# Function to print error message
print_error() {
  echo -e "${RED}✗ ERROR:${NC} $1"
}

# Function to print success message
print_success() {
  echo -e "${GREEN}✓ ÉXITO:${NC} $1"
}

# Function to print info message
print_info() {
  echo -e "${BLUE}ℹ INFO:${NC} $1"
}

# Function to print warning message
print_warning() {
  echo -e "${YELLOW}⚠ ADVERTENCIA:${NC} $1"
}

print_header "Starting skills scan"

# Show configuration
print_info "Skills path: $SKILLS_DIR"
if [ "$NO_LLM" = true ]; then
  print_info "LLM mode: ${YELLOW}Disabled${NC}"
else
  print_info "LLM mode: ${GREEN}Enabled${NC}"
fi

# Validate skillspector is installed
print_info "Validating dependencies..."
if ! command -v skillspector &> /dev/null; then
  echo ""
  print_error "skillspector is not installed"
  echo ""
  echo -e "${YELLOW}To install skillspector, visit:${NC}"
  echo -e "${CYAN}https://github.com/NVIDIA/SkillSpector${NC}"
  echo ""
  exit 1
fi
print_success "skillspector is installed"

# Check if directory exists
echo ""
print_info "Validating directory: $SKILLS_DIR"
if [ ! -d "$SKILLS_DIR" ]; then
  echo ""
  print_error "Directory '$SKILLS_DIR' does not exist"
  echo ""
  exit 1
fi
print_success "Directory found"

# Count total skills
TOTAL_SKILLS=$(find "$SKILLS_DIR" -maxdepth 1 -type d | wc -l)
TOTAL_SKILLS=$((TOTAL_SKILLS - 1)) # Exclude the parent directory itself

echo ""
print_info "Total skills to process: ${CYAN}$TOTAL_SKILLS${NC}"
echo ""

# Initialize counters
PROCESSED=0
SUCCESS=0
FAILED=0

# Iterate over each item in the directory
for skill_path in "$SKILLS_DIR"/*; do
  # Check if it's a directory
  if [ -d "$skill_path" ]; then
    # Get the skill name (basename of the path)
    skill_name=$(basename "$skill_path")
    
    PROCESSED=$((PROCESSED + 1))
    echo -e "${BLUE}[${PROCESSED}/${TOTAL_SKILLS}]${NC} Processing: ${CYAN}$skill_name${NC}"
    
    # Define the output file path
    output_file="$SKILLS_DIR/${skill_name}/evals/${skill_name}.md"
    
    # Ensure the output directory exists
    if ! mkdir -p "$(dirname "$output_file")"; then
      print_error "Could not create directory for $skill_name"
      FAILED=$((FAILED + 1))
      echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"
      continue
    fi
    
    # Execute skillspector scan
    print_info "Running scan: skillspector scan"
    SKILLSPECTOR_CMD="skillspector scan \"$skill_path\" --format markdown --output \"$output_file\""
    if [ "$NO_LLM" = true ]; then
      SKILLSPECTOR_CMD="$SKILLSPECTOR_CMD --no-llm"
    fi
    
    if eval "$SKILLSPECTOR_CMD" 2>&1 | sed 's/^/  /'; then
      print_success "$skill_name processed successfully"
      print_info "Output saved to: $output_file"
      SUCCESS=$((SUCCESS + 1))
    else
      print_error "Error processing $skill_name"
      FAILED=$((FAILED + 1))
    fi
    echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"
  fi
done

# Print final summary
echo ""
print_header "Execution summary"
echo -e "${BLUE}Total processed:${NC}  ${CYAN}$PROCESSED${NC}"
echo -e "${GREEN}Successful:${NC}       ${GREEN}$SUCCESS${NC}"
echo -e "${RED}Failed:${NC}           ${RED}$FAILED${NC}"
echo ""

# Exit with appropriate code
if [ $FAILED -eq 0 ]; then
  print_success "All skills were processed successfully"
  echo ""
  exit 0
else
  print_warning "Completed with $FAILED error(s)"
  echo ""
  exit 1
fi
