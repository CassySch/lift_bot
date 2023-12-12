import machine

PIEZO = machine.PWM(machine.Pin(19))

#Left wheel
AIN1 = machine.Pin(26,machine.Pin.OUT)
AIN2 = machine.Pin(27,machine.Pin.OUT)
PWMA = machine.PWM(machine.Pin(33))

#Right wheel
BIN1 = machine.Pin(14,machine.Pin.OUT)
BIN2 = machine.Pin(12,machine.Pin.OUT)
PWMB = machine.PWM(machine.Pin(4))

#Must be high to enable chip
STBY = machine.Pin(27,machine.Pin.OUT)

#Lift motor pins
REV = machine.Pin(13,machine.Pin.OUT)
FWD = machine.Pin(15,machine.Pin.OUT)

#Switch pins
UP= machine.Pin(23,machine.Pin.IN, pull=machine.Pin.PULL_UP)
DOWN = machine.Pin(12,machine.Pin.IN, pull=machine.Pin.PULL_UP)

