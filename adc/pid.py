# TODO: this file will contain all code needed to run the PID process 
# input = target state (either constant or equation)
# output = changes that will be applied to actuators (reaction wheels, magnetorquers)

from simple_pid import PID
import time
pid = PID(1, 0.1, 0.5, setpoint=9)

# Assume we have a system we want to control in controlled_system

while True:
    # Compute new output from the PID according to the systems current value
    control = pid(8)
    print(control)
    time.sleep(.05)
    
    
    # Feed the PID output to the system and get its current value
   
