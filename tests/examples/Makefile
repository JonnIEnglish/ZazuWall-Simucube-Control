CXX = g++
CXXFLAGS = -std=c++11 -Wall
INCLUDES = -I../../lib/SimpleMotionV2 -I../examples/Simucube-Ioni-Activate -I../../src
LIBS = -L../../lib -L../../lib/SimpleMotionV2 -Wl,-rpath,../../lib -Wl,-rpath,../../lib/SimpleMotionV2 -lsimplemotion_control -lsimplemotionv2 -lhidapi-libusb -ltorque_reader

TARGETS = test_motor_control test_torque_reader

.PHONY: all clean

all: $(TARGETS)

test_motor_control: test_motor_control.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)

test_torque_reader: test_torque_reader.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)

clean:
	rm -f $(TARGETS)