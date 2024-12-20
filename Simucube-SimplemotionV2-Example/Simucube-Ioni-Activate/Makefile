# Compiler and flags
CC = clang++
CFLAGS = -std=c++11 -I/opt/homebrew/include/hidapi -I/usr/include/c++/11 -I/usr/include/aarch64-linux-gnu/c++/11 -DWIN32
LDFLAGS = -L/usr/lib/aarch64-linux-gnu -L/usr/lib/gcc/aarch64-linux-gnu/11 -lhidapi-libusb -lstdc++

# Target and sources
TARGET = enable_ioni_configurator
SOURCES = main.cpp

# Default target
all: $(TARGET)

# Linking step
$(TARGET): $(SOURCES) config_comm_defines.h
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) $(LDFLAGS)

# Clean target
clean:
	rm -f $(TARGET)
