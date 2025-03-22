# Compiler and flags
CXX = clang++
CFLAGS = -std=c++11 -Wall -I/home/jonno/ZazuWall-Simucube-Control/lib/SimpleMotionV2
LDFLAGS = -L/home/jonno/ZazuWall-Simucube-Control/lib/SimpleMotionV2 -L/usr/lib/aarch64-linux-gnu -L/usr/lib/gcc/aarch64-linux-gnu/11 -lsimplemotionv2 -lstdc++

# Target and source files
TARGET = smv2_control_demo
SRC = main.cpp

# Default target
all: $(TARGET)

# Linking step
$(TARGET): $(SRC)
	$(CXX) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

# Clean target
clean:
	rm -f $(TARGET)
