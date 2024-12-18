# Compiler
CC = clang++

# Compiler Flags
CFLAGS = -std=c++17 -Iinclude -I/usr/local/include/hidapi -I/opt/homebrew/include/hidapi

# Linker Flags
LDFLAGS = -Llib -L/usr/local/lib -L/opt/homebrew/lib -lhidapi -lsimplemotionv2

# Target executable
TARGET = simucube_controller

# Source files
SOURCES = src/main.cpp src/ioni_config.cpp src/velocity_control.cpp

# Build Rules
all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) $(LDFLAGS)

clean:
	rm -f $(TARGET)
