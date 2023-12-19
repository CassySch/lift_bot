from motor_control import Motors
import pins

lift_bot = Motors(500, 500)
lift_bot.connect()

if not (pins.TOP.value() == 0 and pins.BOTTOM.value() == 0):
    lift_bot.lift_down()
    lift_bot.current_state = lift_bot.STATE_DOWN
if pins.TOP.value() == 0:
    lift_bot.lift_state = "OPEN"
if pins.BOTTOM.value() == 0:
    lift_bot.lift_state = "CLOSED"
else:
    lift_bot.lift_state = "PARTIAL"
while True:
    lift_bot.button_handler()
    lift_bot.motor_control()



