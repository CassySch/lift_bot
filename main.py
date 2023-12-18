from motor_control import Motors
import pins

lift_bot = Motors(500, 500)
lift_bot.connect()

if not (pins.UP.value() == 0 and pins.DOWN.value() == 0):
    lift_bot.lift_down()
    lift_bot.current_state = 9
            
while True:
    lift_bot.button_handler()
    lift_bot.motor_control()
