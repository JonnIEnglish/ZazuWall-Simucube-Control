CXX = g++
CXXFLAGS = -fPIC -Wall -I../lib/SimpleMotionV2 -I/usr/include/python3.10 -std=c++11
LDFLAGS = -shared -L../lib -lsimplemotionv2 -lpython3.10

# Python bindings output
PYBIND_MODULE = ionispeed

all: ../lib/libtorque_reader.so ../lib/$(PYBIND_MODULE).so

# Torque reader remains unchanged
../lib/libtorque_reader.so: continuous_torque_reader.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

# New set_speed build rule
../lib/$(PYBIND_MODULE).so: set_speed.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f ../lib/libtorque_reader.so ../lib/$(PYBIND_MODULE).so
