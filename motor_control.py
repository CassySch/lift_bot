import machine
import network
import usocket as socket
import time
import random
import pins

# Lift bot states
# 1: "Forward",
# 2: "Backward",
# 3: "Left",
# 4: "Right",
# 5: "Backwards right",
# 6: "Backwards left",
# 7: "Stopped",
# 8: "Lift up",
# 9: "Lift Down",
# 10: "Lift motor stop"
# 11: "Startup"


class Motors:

    def __init__(self, duty, freq):
        # Constructor, called when an object is created
        self.pins = pins
        self.pins.PWMA.duty(duty)
        self.pins.PWMB.duty(duty)

        self.pins.PWMA.freq(freq)
        self.pins.PWMB.freq(freq)
        self.decoded_data = ""
        self.previous_data = ""
        self.server_socket = None  # Initialize as None
        self.current_state = 11  # startup
        self.lift_state = 'UNKNOWN'
    def connect(self):
        # Use esp as access point
        ssid = 'ESP32-Router'
        password = 'your-password'

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password)

        print('AP IP address:', ap.ifconfig()[0])

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', 12345))
        self.server_socket.listen(1)

        Motors.continue_listening = True

    def button_handler(self):
        # listen for a connection as long a previous connection was not terminated
        while Motors.continue_listening:
            print('Waiting for connections...')
            conn, addr = self.server_socket.accept()
            print('Connected by', addr)
            conn.sendall('Hello from ESP32 Access Point!'.encode())
            while True:
                data = conn.recv(1024)
                if not data:
                    # No more data, break from the inner loop
                    break
                self.decoded_data = data.decode('utf-8')
                self.pevious_data = self.decoded_data
                self.motor_control()
                print('Decoded:', self.decoded_data)
                # Close connection
                if Motors.continue_listening == False:
                    conn.close()  # Close the connection
                    break  # Break from the inner loop
                state = str(self.current_state)
                states = state + ',' + self.lift_state
                conn.sendall(states.encode())
                print("Sent state")
    def is_new_data(self):
        return self.decoded_data != self.previous_data

    def motor_control(self):
            if pins.UP.value() == 0:
                self.lift_state = 'OPEN'
            elif pins.DOWN.value() == 0:
                self.lift_state = 'CLOSED'
            else:
                self.lift_state = 'UNKNOWN'
            if self.current_state ==  1:  # Forward
                self.go_forward()
                if self.is_new_data():
                    self.current_state = 7

            if self.current_state == 2:  # Backward
                self.go_backward()
                if self.is_new_data():
                    self.current_state = 7

            if self.current_state == 3:  # Left
                self.go_left()
                if self.is_new_data():
                    self.current_state = 7
            if self.current_state == 4:  # Right
                self.go_right()
                if self.is_new_data():
                    self.current_state = 7
            # case 5:  # Bacwards Right only to be added if using joy stick
            # case 6:  # Bacwards Left
            if self.current_state == 7:  # Stopped
                print("In state 7")
                if pins.UP.value() == 0 or pins.DOWN.value() == 0:  # Lift is completely extended or closed
                        print("In state 7 ready to move")
                        if self.decoded_data ==  'a,1':
                            #if self.decoded_data == 'a,0':
                            self.current_state = 4
                        if self.decoded_data ==  'x,1':
                            #if self.decoded_data == 'x,0':
                            self.current_state = 1
                        if self.decoded_data == 'b,1':
                            #if self.decoded_data == 'b,0':
                            self.current_state = 2
                        if self.decoded_data == 'y,1':
                            #if self.decoded_data == 'y,0':
                            self.current_state = 3
                        if self.decoded_data == 'zr,1':
                            #if self.decoded_data == 'zr,1':
                            if pins.UP.value() == 0:
                                self.current_state = 9
                            elif pins.DOWN.value() == 0:
                                self.current_state = 8
                else:
                    self.current_state = 11
            if self.current_state == 8:  # Lift go Up
                pins.REV.value(0)
                pins.FWD.value(1)
                if pins.UP.value() == 0:
                    self.current_state = 10
            if self.current_state == 9:  # Lift go down
                pins.REV.value(1)
                pins.FWD.value(0)
                if pins.DOWN.value() == 0:
                    self.current_state = 10
            if self.current_state == 10:  # Lift motor stop
                if pins.UP.value() == 0 or pins.DOWN.value() == 0:
                    pins.FWD.value(0)
                    pins.REV.value(0)
                    self.current_state = 7
            if self.current_state == 11:  # Startup
                if pins.UP.value() != 0 or pins.DOWN.value() != 0:
                    self.current_state = 9
                else:
                    self.current_state = 7
            if self.decoded_data == 'r,1':
                    print("Exiting")
                    PWMA.duty(0)
                    PWMB.duty(0)
                    Motors.continue_listening = False  # Stop looking for new connections
            print("Current state:", self.current_state)
            print("Type", type(self.current_state))
            print("Up:", pins.UP.value())
            
    def go_right(self):
        print("Right")
        pins.AIN1.value(1)
        pins.AIN2.value(0)
        pins.PWMA.duty(500)

    def go_backward(self):
        print("Backward")
        pins.AIN1.value(0)
        pins.AIN2.value(1)
        pins.PWMA.duty(500)

        pins.BIN1.value(0)
        pins.BIN2.value(1)
        pins.PWMB.duty(500)

    def go_forward(self):
        print("Forward")
        pins.AIN1.value(1)
        pins.AIN2.value(0)
        pins.PWMA.duty(500)

        pins.BIN1.value(1)
        pins.BIN2.value(0)
        pins.PWMB.duty(500)

    def go_left(self):
        print("Left")
        pins.BIN1.value(1)
        pins.BIN2.value(0)
        pins.PWMB.duty(500)

    def stop(self):
        print("Stopped")
        pins.PWMA.duty(0)
        pins.PWMB.duty(0)



