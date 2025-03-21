CXX = g++
CXXFLAGS = -std=c++11 -Wall
INCLUDES = -I../../lib/SimpleMotionV2 -I../examples/Simucube-Ioni-Activate
LIBS = -L../../lib -L../../lib/SimpleMotionV2 -Wl,-rpath,../../lib -Wl,-rpath,../../lib/SimpleMotionV2 -lsimplemotion_control -lsimplemotionv2 -lhidapi-libusb

TARGET = test_motor_control
SOURCES = test_motor_control.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)

clean:
	rm -f $(TARGET)