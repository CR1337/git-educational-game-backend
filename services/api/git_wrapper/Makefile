CC = gcc

SRC_COMMON = communication.c debug.c init.c util.c
SRC_ORCH = orchestrator.c
SRC_EDITOR = editor_simulator.c

BUILD_DIR = build

CFLAGS_COMMON = -Wall -Wextra -fPIC
CFLAGS_TEST = -O0 -g -DDEBUG
CFLAGS_PROD = -O2

LDFLAGS_SO = -shared

TARGET_ORCH = $(BUILD_DIR)/orchestrator
TARGET_EDITOR = $(BUILD_DIR)/editor_simulator
TARGET_SO = $(BUILD_DIR)/libcommunication.so
PY_WRAPPER = $(BUILD_DIR)/communication.py

.PHONY: test prod clean dirs postbuild

# -------- TEST BUILD --------

test: CFLAGS = $(CFLAGS_COMMON) $(CFLAGS_TEST)
test: dirs $(TARGET_ORCH) $(TARGET_EDITOR) $(TARGET_SO) postbuild

# -------- PROD BUILD --------

prod: CFLAGS = $(CFLAGS_COMMON) $(CFLAGS_PROD)
prod: dirs $(TARGET_ORCH) $(TARGET_EDITOR) $(TARGET_SO) postbuild

# -------- DIRECTORY --------

dirs:
	mkdir -p $(BUILD_DIR)

# -------- EXECUTABLES --------

$(TARGET_ORCH): $(SRC_ORCH) $(SRC_COMMON)
	$(CC) $(CFLAGS) $^ -o $@

$(TARGET_EDITOR): $(SRC_EDITOR) $(SRC_COMMON)
	$(CC) $(CFLAGS) $^ -o $@

# -------- SHARED LIBRARY --------

$(TARGET_SO): $(SRC_COMMON)
	$(CC) $(CFLAGS) $(LDFLAGS_SO) $^ -o $@

# -------- POST BUILD STEPS --------

postbuild: $(TARGET_SO)
	ctypesgen communication.h --library $(TARGET_SO) -o $(PY_WRAPPER) 2>/dev/null
	chmod +x $(TARGET_ORCH)
	chmod +x $(TARGET_EDITOR)

# -------- CLEAN --------

clean:
	rm -rf $(BUILD_DIR)