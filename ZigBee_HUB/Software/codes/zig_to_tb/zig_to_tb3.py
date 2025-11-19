import paho.mqtt.client as mqtt
import json
import time
import random

# Zigbee2MQTT topic
zigbee_sub = "zigbee2mqtt/Zigbee_InWall"
zigbee_pub = "zigbee2mqtt/Zigbee_InWall/set"

# ThingsBoard settings
THINGSBOARD_HOST = 'tb2.thingsware.cloud'
ACCESS_TOKEN = 'p77W8xKy97SDhhKEX6VS'  # Replace with your device token

# Handle connection to ThingsBoard
def on_connect_tb(client, userdata, flags, rc):
    print("Connected to ThingsBoard:", rc)
    client.subscribe('v1/devices/me/rpc/request/+')  # Subscribe to RPC calls

# Handle connection to Zigbee2MQTT
def on_connect_zigbee(client, userdata, flags, rc):
    print("Connected to Zigbee2MQTT:", rc)
    client.subscribe(zigbee_sub)  # Subscribe to Zigbee device status

# Handle incoming messages from Zigbee2MQTT
def on_message_zigbee(client, userdata, msg):
    print("Zigbee2MQTT →", msg.payload.decode())
    try:
        data = json.loads(msg.payload.decode())
        if 'state' in data:
            telemetry = {"Linkquality" : data['linkquality'], "LED": data['state']}
            attribute = {"Linkquality" : data['linkquality'], "LED": data['state']}
            tb_client.publish('v1/devices/me/telemetry', json.dumps(telemetry), 1)
            tb_client.publish('v1/devices/me/attributes', json.dumps(attribute), 1)
    except Exception as e:
        print("Error parsing Zigbee2MQTT message:", e)

# Handle incoming RPC messages from ThingsBoard
def on_message_tb(client, userdata, msg):
    print("ThingsBoard RPC →", msg.payload.decode())
    try:
        request_id = msg.topic.split('/')[-1]  # Extract the request ID from topic
        payload = json.loads(msg.payload.decode())

        if payload.get("method") == "setLED":
            desired_state = payload.get("params")

            #zigbee_state = "ON" if desired_state else "OFF"
            # Send the LED state to Zigbee device
            zigbee_client.publish(zigbee_pub, json.dumps({"state": desired_state}), 1)

            # Send response back to ThingsBoard to prevent timeout
            response = {"result": f"LED set to {desired_state}"}
            client.publish(f'v1/devices/me/rpc/response/{request_id}', json.dumps(response), 1)

    except Exception as e:
        print("Error parsing TB message:", e)

# Setup Zigbee MQTT client
zigbee_client = mqtt.Client(f"zigbee_{random.randint(1000,9999)}")
zigbee_client.on_connect = on_connect_zigbee
zigbee_client.on_message = on_message_zigbee
zigbee_client.connect("localhost", 1883)

# Setup ThingsBoard MQTT client
tb_client = mqtt.Client(f"tb_{random.randint(1000,9999)}")
tb_client.username_pw_set(ACCESS_TOKEN)
tb_client.on_connect = on_connect_tb
tb_client.on_message = on_message_tb
tb_client.connect(THINGSBOARD_HOST, 1883)

# Start both MQTT loops
zigbee_client.loop_start()
tb_client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")

# Clean stop
zigbee_client.loop_stop()
tb_client.loop_stop()


