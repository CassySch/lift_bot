import network
import usocket as socket
import pins
import select


EVENT_DISCONNECT = 'r,1'
EVENT_LEFT = 'y,1'
EVENT_BACKWARD = 'b,1'
EVENT_FORWARD = 'x,1'
EVENT_RIGHT = 'a,1'
EVENT_LIFT = 'zr,1'

EVENT_DISCONNECT_RELEASE = 'r,0'
EVENT_LEFT_RELEASE = 'y,0'
EVENT_BACKWARD_RELEASE = 'b,0'
EVENT_FORWARD_RELEASE = 'x,0'
EVENT_RIGHT_RELEASE = 'a,0'
EVENT_LIFT_RELEASE = 'zr,0'

STATE_FORWARD = 1
STATE_BACKWARD = 2
STATE_LEFT = 3
STATE_RIGHT = 4
STATE_IDLE = 7
STATE_DOWN = 9
STATE_UP = 8


class Motors:
    def __init__(self, duty, freq):
        # Constructor, called when an object is created
        self.pins = pins
        self.pins.PWMA.duty(duty)
        self.pins.PWMB.duty(duty)

        self.pins.PWMA.freq(freq)
        self.pins.PWMB.freq(freq)
        
        self.pins.REV.value(0)
        self.pins.FWD.value(0)
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
        if self.is_new_data():
            button_event = self.current_data
            self.previous_data = self.current_data

            if button_event == EVENT_DISCONNECT:
                print("Exiting")
                self.stop_all()
                self.client_socket.close()  # Close the client socket
                return

        move_event = (button_event == EVENT_FORWARD or button_event == EVENT_LEFT or button_event == EVENT_RIGHT
                      or button_event == EVENT_BACKWARD or button_event == EVENT_FORWARD_RELEASE
                      or button_event == EVENT_LEFT_RELEASE or button_event == EVENT_RIGHT_RELEASE
                      or button_event == EVENT_BACKWARD_RELEASE)


        state = str(self.current_state)
        machine_state_tag = "machine"
        machine = f"{machine_state_tag},{state}"
        self.client_socket.sendall(machine.encode())

        lift_state_str = self.lift_state
        lift_state_tag = "stateLf"
        lift = f"{lift_state_tag},{lift_state_str}"
        self.client_socket.sendall(lift.encode())


        print("Sent state")

        if pins.TOP.value() == 0:
            self.lift_state = 'OPEN'
        elif pins.BOTTOM.value() == 0:
            self.lift_state = 'CLOSED'
        else:
            self.lift_state = 'PARTIAL'

        if self.current_state == STATE_FORWARD:
            if move_event and not move_event == EVENT_FORWARD:
                self.go_idle()
            else:
                self.go_continue_move()

        elif self.current_state == STATE_BACKWARD:
            if move_event and not move_event == EVENT_BACKWARD:
                self.go_idle()
            else:
                self.go_continue_move()

        elif self.current_state == STATE_LEFT:
            if move_event and not move_event == EVENT_LEFT:
                self.go_idle()
            else:
                self.go_continue_move()

        elif self.current_state == STATE_RIGHT:
            if move_event and not move_event == EVENT_RIGHT:
                self.go_idle()
            else:
                self.go_continue_move()

        # case 5:  # Backwards Right only to be added if using joy stick
        # case 6:  # Backwards Left
        elif self.current_state == STATE_IDLE:
            print("In state 7")
            if pins.TOP.value() == 0 or pins.BOTTOM.value() == 0:  # Lift is completely extended or closed
                print("In state 7 ready to move")
                if button_event == EVENT_RIGHT:
                    # if self.decoded_data == 'a,0':
                    self.go_right()
                    self.current_state = STATE_RIGHT
                elif button_event == EVENT_FORWARD:
                    # if self.decoded_data == 'x,0':
                    self.go_forward()
                    self.current_state = STATE_FORWARD
                elif button_event == EVENT_BACKWARD:
                    # if self.decoded_data == 'b,0':
                    self.go_backward()
                    self.current_state = STATE_BACKWARD
                elif button_event == EVENT_LEFT:
                    # if self.decoded_data == 'y,0':
                    self.go_left()
                    self.current_state = STATE_LEFT
                elif button_event == EVENT_LIFT:
                    # if self.decoded_data == 'zr,1':
                    if pins.BOTTOM.value() != 0:
                        self.lift_down()
                        self.current_state = STATE_DOWN
                    elif pins.TOP.value() != 0:
                        self.lift_up()
                        self.current_state = STATE_UP

        elif self.current_state == STATE_UP:
            if pins.TOP.value() == 0:
                self.lift_stop()
                self.current_state = STATE_IDLE

        elif self.current_state == STATE_DOWN:
            if pins.BOTTOM.value() == 0:
                self.lift_stop()
                self.current_state = STATE_IDLE

        print("Current state:", self.current_state)
        print("Up:", pins.TOP.value())
        print("Down", pins.BOTTOM.value())
        print("Old:", self.current_data)
        print("New:", self.previous_data)

    def go_continue_move(self):
        # pins.PIEZO.duty(0)
        return

    def go_idle(self):
        # pins.PIEZO.duty(500)
        # pins.PIEZO.freq(50)
        self.stop()
        self.current_state = STATE_IDLE
        return

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
