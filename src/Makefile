CXX = g++
CXXFLAGS = -std=c++11 -Wall -I../lib/SimpleMotionV2 -fPIC
LDFLAGS = -L../lib/SimpleMotionV2 -L../lib -lsimplemotionv2 -shared

TARGET = ../lib/libsimplemotion_control.so
SOURCES = simplemotion_control.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGET)