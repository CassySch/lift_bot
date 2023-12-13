from motor_control import Motors

lift_bot = Motors(300, 500)
while True:
    lift_bot.connect()
    lift_bot.button_handler()

