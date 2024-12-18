CXX = clang++
CXXFLAGS = -std=c++11 -Wall -I/Users/jonno/GitProjects/ZazuWall-Simucube-Control/Simucube-SimplemotionV2-Example/SimplemotionV2-Speed-Setpoint/SimpleMotionV2
LDFLAGS = -L/Users/jonno/GitProjects/ZazuWall-Simucube-Control/Simucube-SimplemotionV2-Example/SimplemotionV2-Speed-Setpoint/SimpleMotionV2 -lsimplemotionv2
TARGET = smv2_control_demo
SRC = main.cpp
all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)