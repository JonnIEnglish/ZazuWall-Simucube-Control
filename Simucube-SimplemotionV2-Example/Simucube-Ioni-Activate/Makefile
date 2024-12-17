CC = clang++
CFLAGS = -std=c++11 -I/opt/homebrew/include/hidapi -DWIN32
LDFLAGS = -L/opt/homebrew/lib -lhidapi
TARGET = enable_ioni_configurator
SOURCES = main.cpp

all: $(TARGET)

$(TARGET): $(SOURCES) config_comm_defines.h
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) $(LDFLAGS)

clean:
	rm -f $(TARGET)