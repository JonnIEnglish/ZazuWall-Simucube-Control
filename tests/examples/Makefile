CXX = g++
CXXFLAGS = -std=c++11 -Wall
LDFLAGS = -L../../lib -L../../lib/SimpleMotionV2 -lsimplemotion_control -lsimplemotionv2

TARGET = test_motor_control
SOURCES = test_motor_control.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGET)