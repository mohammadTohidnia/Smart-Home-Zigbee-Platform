import OPi.GPIO as gpio
import time
import subprocess
import threading
import paho.mqtt.client as mqtt
import json

# Define GPIO pins
WIFI_LED = 'PC9'
MQTT_LED = 'PC6'
PAIR_LED = 'PC5'
PAIR_BUTTON = 'PC1'

# Setup GPIO
gpio.setmode(gpio.SUNXI)
gpio.setup(WIFI_LED, gpio.OUT)
gpio.setup(MQTT_LED, gpio.OUT)
gpio.setup(PAIR_LED, gpio.OUT)
gpio.setup(PAIR_BUTTON, gpio.IN, pull_up_down=gpio.PUD_UP)

# Global flags
mqtt_connected = False
z2m_online = False
pairing_mode = False

# Functions
def is_wifi_connected():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "DEVICE,STATE", "dev"], universal_newlines=True)
        for line in result.splitlines():
            if line.startswith("wlan0:"):
                state = line.split(":")[1]
                return state == "connected"
    except Exception as e:
        print(f"Error checking Wi-Fi status: {e}")
    return False

def LED_Blink(led_pin, blink_time):
    gpio.output(led_pin, 1)
    time.sleep(blink_time)
    gpio.output(led_pin, 0)
    time.sleep(blink_time)

def wifi_led_thread():
    Delay_Time = 3
    while True:
        if is_wifi_connected():
            gpio.output(WIFI_LED, 1)
            print("Connected to Wi-Fi")
            time.sleep(Delay_Time)
        else:
            print("Wi-Fi disconnected, blinking...")
            for _ in range(int(Delay_Time / 0.6)):
                LED_Blink(WIFI_LED, 0.3)

def mqtt_led_thread():
    Delay_Time = 3
    while True:
        if mqtt_connected and z2m_online:
            gpio.output(MQTT_LED, 1)
            print("Zigbee2MQTT is online")
            time.sleep(Delay_Time)
        else:
            print("Zigbee2MQTT is offline or MQTT disconnected, blinking...")
            for _ in range(int(Delay_Time / 0.6)):
                LED_Blink(MQTT_LED, 0.3)

def permit_join_thread():
    global pairing_mode
    while True:
        if gpio.input(PAIR_BUTTON) == 0:  # Button pressed
            start_time = time.time()
            while gpio.input(PAIR_BUTTON) == 0:
                time.sleep(0.1)
                if time.time() - start_time >= 3:
                    print("Button held for 3 seconds. Enabling pairing mode...")
                    pairing_mode = True
                    client.publish("zigbee2mqtt/bridge/request/permit_join", json.dumps({"value": True, "time": 120}))
                    
                    # Blink fast for 5 seconds
                    start_blink = time.time()
                    while time.time() - start_blink < 5:
                        LED_Blink(PAIR_LED, 0.1)
                    
                    gpio.output(PAIR_LED, 0)  # Ensure LED off
                    pairing_mode = False
                    break
        time.sleep(0.1)

def device_message_blink_thread():
    while True:
        if device_message_event.wait():
            if not pairing_mode:
                LED_Blink(PAIR_LED, 0.1)
            device_message_event.clear()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = (rc == 0)
    if mqtt_connected:
        print("MQTT Connected")
        client.subscribe("zigbee2mqtt/bridge/state")
        client.subscribe("zigbee2mqtt/#")
    else:
        print(f"MQTT Failed with code {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("MQTT Disconnected")

def on_message(client, userdata, msg):
    global z2m_online

    if msg.topic == "zigbee2mqtt/bridge/state":
        payload = msg.payload.decode()
        print(payload)
        if "online" in payload:
            z2m_online = True
        else:
            z2m_online = False
        print(f"Zigbee2MQTT state: {payload}")
    
    elif msg.topic.startswith("zigbee2mqtt/") and not msg.topic.startswith("zigbee2mqtt/bridge/"):
        print(f"Device message: {msg.topic}")
        device_message_event.set()

# Setup MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect_async("localhost", 1883, 60)
client.loop_start()

# Events
device_message_event = threading.Event()

# Start threads
threads = [
    threading.Thread(target=wifi_led_thread, daemon=True),
    threading.Thread(target=mqtt_led_thread, daemon=True),
    threading.Thread(target=permit_join_thread, daemon=True),
    threading.Thread(target=device_message_blink_thread, daemon=True)
]

for t in threads:
    t.start()

# Keep main thread alive
try:
    gpio.output(MQTT_LED, 0)
    gpio.output(PAIR_LED, 0)
    while True:
        time.sleep(1)
        print("Button state:", gpio.input(PAIR_BUTTON))
except KeyboardInterrupt:
    gpio.cleanup()
    client.loop_stop()
    client.disconnect()
