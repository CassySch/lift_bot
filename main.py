from motor_control import Motors

lift_bot = Motors(500, 500)
lift_bot.connect()
while True:
    lift_bot.button_handler()
    lift_bot.motor_control()
