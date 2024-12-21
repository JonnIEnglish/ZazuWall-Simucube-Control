# Compiler and flags
CXX = clang++
CXXFLAGS = -std=c++11 -Wall -fPIC \
    -I/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/SimpleMotionV2
LDFLAGS = -L/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/SimpleMotionV2 -lsimplemotionv2 \
    -L/usr/lib/aarch64-linux-gnu -L/usr/lib/gcc/aarch64-linux-gnu/11 -lstdc++

# Target and source files
TARGET = libsimucube.so
SRC = /home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/simucube_lib.c

# Default target
all: $(TARGET)

# Building shared library
$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -shared -o $(TARGET) $(SRC) $(LDFLAGS)

# Clean target
clean:
	rm -f $(TARGET)
