# Variables
RED=\033[31m
GREEN=\033[32m
YELLOW=\033[33m
BLUE=\033[34m
NOCOLOR=\033[0m

GIT_HOOKS_DIR = .git/hooks
COMMIT_MSG_HOOK = $(GIT_HOOKS_DIR)/commit-msg

# Ejecución por defecto (se ejecuta al correr 'make')
all: hooks

# Crear hooks de Git
hooks: commit-msg
	@echo -e "$(GREEN)Git hooks created successfully. $(NOCOLOR)"

# Commit-msg hook
commit-msg:
	@echo -e "$(BLUE)Creating commit-msg hook... $(NOCOLOR)"
	@mkdir -p $(GIT_HOOKS_DIR)
	@cp scripts/commit-msg $(COMMIT_MSG_HOOK)
	@chmod +x $(COMMIT_MSG_HOOK)
	@echo -e "$(GREEN)Commit-msg hook set up. $(NOCOLOR)"

# Limpiar hooks (opcional)
remove-hooks:
	@echo -e "$(GREEN)Removing git hooks... $(NOCOLOR)"
	@rm -f $(COMMIT_MSG_HOOK)
	@echo -e "$(GREEN)Git hooks removed. $(NOCOLOR)"
