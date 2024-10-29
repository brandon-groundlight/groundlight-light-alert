import tinytuya
import os
import random
import time

SWITCH_REGION = os.getenv("SWITCH_REGION") if os.getenv("SWITCH_REGION") else "us"
SWITCH_API_KEY = os.getenv("SWITCH_API_KEY")
SWITCH_API_SECRET = os.getenv("SWITCH_API_SECRET")
SWITCH_ID = os.getenv("SWITCH_ID")

if not SWITCH_API_KEY:
    raise ValueError("SWITCH_API_KEY not set")
if not SWITCH_API_SECRET:
    raise ValueError("SWITCH_API_SECRET not set")

cloud_connection = tinytuya.Cloud(tuya_region=SWITCH_REGION, access_id=SWITCH_API_KEY, access_key=SWITCH_API_SECRET)

class SwitchManager():

    ON_COMMAND = {
        'commands': [{
            'code': 'switch_1',
            'value': True
        }]
    }
    OFF_COMMAND = {
        'commands': [{
            'code': 'switch_1',
            'value': False
        }]
    }

    def __init__(self, switch_id):
        self.switch_id = switch_id

    def turn_on(self):
        cloud_connection.sendcommand(self.switch_id, self.ON_COMMAND)

    def turn_off(self):
        cloud_connection.sendcommand(self.switch_id, self.OFF_COMMAND)

    def go_ham(self):
        for _ in range(10):
            self.turn_on()
            self.turn_off()

    def spook(self):
        self.turn_on()
        time.sleep(5)
        self.turn_off()