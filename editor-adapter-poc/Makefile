CC = gcc
CFLAGS = -Wall -Wextra
OPTIMIZE = -O2
DEBUG_FLAGS = -O0 -D_DEBUG -g

TARGET = editor-adapter
TEST_TARGET = test-editor-adapter

SRC_MAIN = main.c sockets.c
SRC_TEST = test.c sockets.c

all: $(TARGET) $(TEST_TARGET)

$(TARGET): $(SRC_MAIN)
	$(CC) $(CFLAGS) $(OPTIMIZE) -o $@ $^

$(TEST_TARGET): $(SRC_TEST)
	$(CC) $(CFLAGS) $(OPTIMIZE) -o $@ $^

debug: CFLAGS += $(DEBUG_FLAGS)

debug: $(TARGET) $(TEST_TARGET)

clean:
	rm -f $(TARGET) $(TEST_TARGET)
