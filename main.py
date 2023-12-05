import config
import machine
import network
import socket

# motor1A = machine.Pin(18, machine.Pin.OUT)
# motor1B = machine.Pin(25, machine.Pin.OUT)
# motor1C = machine.Pin(26, machine.Pin.OUT)
# stby = machine.Pin(27, machine.Pin.OUT)
# pwma = machine.Pin(33, machine.Pin.OUT)
lift_up = machine.Pin(15,machine.Pin.OUT)
lift_down = machine.Pin(13,machine.Pin.OUT)
# piezo = machine.PWM(machine.Pin(19))

while 1:
    lift_up.value(1)
    lift_down.value(0)
