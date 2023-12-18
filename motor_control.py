import network
import usocket as socket
import time
import pins
import select

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
        self.current_data = ""
        self.server_socket = None  # Initialize as None
        self.current_state = 7  # startup
        self.lift_state = 'UNKNOWN'
        self.client_socket = None
        self.continue_listening = True

    def connect(self):
        # Use esp as access point
        ssid = 'ESP32-Router'
        password = 'your-password'

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password)

        print('AP IP address:', ap.ifconfig()[0])

        # Register the server socket for accepting new connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', 12345))
        self.server_socket.listen()

        # Accept a new connection as long as the previous connection was not terminated
        print('Waiting for connections...')
        while self.continue_listening:
            self.client_socket, addr = self.server_socket.accept()
            print('Connected by', addr)
            self.client_socket.sendall('Hello from ESP32 Access Point!'.encode())
            self.continue_listening = False
       

    def button_handler(self):
        while True:
            try:
                rlist, _, _ = select.select([self.client_socket], [], [], 0.5)

                if self.client_socket in rlist:
                    data = self.client_socket.recv(1024)

                    if data:
                        print("Old:", self.current_data)
                        print("New:", self.previous_data)
                        self.decoded_data = data.decode('utf-8')
                        self.previous_data = self.current_data
                        self.current_data = self.decoded_data
                        print('Decoded:', self.decoded_data)
                        print("Old:", self.current_data)
                        print("New:", self.previous_data)
                else:
                    break
            except OSError as e:
                if e.args[0] == 11:  # EAGAIN
                    pass  # No data available, continue waiting
                else:
                    raise


           
            
    def is_new_data(self):
        return self.current_data != self.previous_data

    def motor_control(self):
        button_event = ""
        motor_message = "Entering Motor control"
        motor_tag = "motor"
        entering = f"{motor_tag},{motor_message}"
        self.client_socket.sendall(entering.encode())
        if self.is_new_data():
            button_event = self.current_data
            self.previous_data = self.current_data
            
        move_event = button_event == 'x,1' or button_event == 'y,1' or button_event == 'a,1' or button_event == 'b,1'
        
        if not (pins.UP.value() == 0 and pins.DOWN.value() == 0):
            self.lift_down()
            self.current_state = 9
        while True:
            loop_message = "Motor Control Loop"
            loop_tag = "loop"
            loop = f"{loop_tag},{loop_message}"
            
            prev_state = self.current_state
            
            state = str(self.current_state)
            machine_state_tag = "machine"
            machine = f"{machine_state_tag},{state}"
            
            lift_state_str = self.lift_state
            lift_state_tag = "stateLf"
            lift = f"{lift_state_tag},{lift_state_str}"
            
            combined_data = f"{loop_tag},{loop_message};{machine_state_tag},{state};{lift_state_tag},{lift_state_str}"
            #self.client_socket.sendall(combined_data.encode())
            
            print("Sent state")

            if pins.UP.value() == 0:
                self.lift_state = 'OPEN'
            elif pins.DOWN.value() == 0:
                self.lift_state = 'CLOSED'
            else:
                self.lift_state = 'PARTIAL'

            if self.current_state == 1:  # Forward
                if move_event:
                    pins.PIEZO.duty(500)
                    pins.PIEZO.freq(50)
                    self.stop()
                    self.current_state = 7
                else:
                    pins.PIEZO.duty(0)

            elif self.current_state == 2:  # Backward
                if move_event:
                    pins.PIEZO.duty(500)
                    pins.PIEZO.freq(50)
                    self.stop()
                    self.current_state = 7
                else:
                    pins.PIEZO.duty(0)

            elif self.current_state == 3:  # Left
                if move_event:
                    pins.PIEZO.duty(500)
                    pins.PIEZO.freq(50)
                    self.stop()
                    self.current_state = 7
                else:
                    pins.PIEZO.duty(0)

            elif self.current_state == 4:  # Right
                if move_event:
                    pins.PIEZO.duty(500)
                    pins.PIEZO.freq(50)
                    self.stop()
                    self.current_state = 7
                else:
                    pins.PIEZO.duty(0)

            # case 5:  # Bacwards Right only to be added if using joy stick
            # case 6:  # Bacwards Left
            elif self.current_state == 7:  # Movement State
                print("In state 7")
                if pins.UP.value() == 0 or pins.DOWN.value() == 0:  # Lift is completely extended or closed
                    print("In state 7 ready to move")
                    if button_event == 'a,1':
                        # if self.decoded_data == 'a,0':
                        button_event = ""
                        move_event = False
                        self.go_right()
                        self.current_state = 4
                    elif button_event== 'x,1':
                        # if self.decoded_data == 'x,0':
                        button_event = ""
                        move_event = False
                        self.go_forward()
                        self.current_state = 1
                    elif button_event == 'b,1':
                        # if self.decoded_data == 'b,0':
                        button_event = ""
                        move_event = False
                        self.go_backward()
                        self.current_state = 2
                    elif button_event == 'y,1':
                        # if self.decoded_data == 'y,0':
                        button_event = ""
                        move_event = False
                        self.go_left()
                        self.current_state = 3
                    elif button_event == 'zr,1':
                        # if self.decoded_data == 'zr,1':
                        if pins.DOWN.value() != 0:
                            button_event = ""
                            move_event = False
                            self.lift_down()
                            self.current_state = 9
                        elif pins.UP.value() != 0:
                            button_event = ""
                            move_event = False
                            self.lift_up()
                            self.current_state = 8
                    if button_event == 'r,1':
                        print("Exiting")
                        self.stop_all()
                        self.client_socket.close()  # Close the client socket

            elif self.current_state == 8:  # Lift going Up
                if pins.UP.value() == 0:
                    self.lift_stop()
                    self.current_state = 7

            elif self.current_state == 9:  # Lift going down
                if pins.DOWN.value() == 0:
                    self.lift_stop()
                    self.current_state = 7

            if button_event == 'r,1':
                print("Exiting")
                self.stop_all()
                self.client_socket.close()  # Close the client socket

            print("Current state:", self.current_state)
            print("Type", type(self.current_state))
            print("Up:", pins.UP.value())
            print("Down", pins.DOWN.value())
            print("Old:", self.current_data)
            print("New:", self.previous_data)

            if prev_state == self.current_state:
                break
            
    def go_right(self):
        print("Right")
        pins.AIN1.value(1)
        pins.AIN2.value(0)
        pins.PWMA.duty(750)

        pins.BIN1.value(1)
        pins.BIN2.value(0)
        pins.PWMB.duty(750)

    def go_backward(self):
        print("Backward")
        pins.AIN1.value(0)
        pins.AIN2.value(1)
        pins.PWMA.duty(750)

        pins.BIN1.value(1)
        pins.BIN2.value(0)
        pins.PWMB.duty(750)

    def go_forward(self):
        print("Forward")
        pins.AIN1.value(1)
        pins.AIN2.value(0)
        pins.PWMA.duty(750)

        pins.BIN1.value(0)
        pins.BIN2.value(1)
        pins.PWMB.duty(750)

    def go_left(self):
        print("Left")
        pins.BIN1.value(0)
        pins.BIN2.value(1)
        pins.PWMB.duty(750)

        pins.AIN1.value(0)
        pins.AIN2.value(1)
        pins.PWMA.duty(750)

    def lift_stop(self):
        print("Stopped")
        pins.FWD.value(0)
        pins.REV.value(0)

    def lift_up(self):
        pins.REV.value(0)
        pins.FWD.value(1)
        pins.PWMA.duty(0)
        pins.PWMB.duty(0)

    def lift_down(self):
        pins.REV.value(1)
        pins.FWD.value(0)
        pins.PWMA.duty(0)
        pins.PWMB.duty(0)

    def stop(self):
        pins.PWMA.duty(0)
        pins.PWMB.duty(0)

    def stop_all(self):
        pins.PWMA.duty(0)
        pins.PWMB.duty(0)
        pins.FWD.value(0)
        pins.REV.value(0)

