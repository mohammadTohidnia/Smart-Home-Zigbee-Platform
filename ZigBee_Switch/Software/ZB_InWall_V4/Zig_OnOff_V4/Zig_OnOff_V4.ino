
#ifndef ZIGBEE_MODE_ED
#error "Zigbee end device mode is not selected in Tools->Zigbee mode"
#endif

#include "Zigbee.h"

/* Zigbee light bulb configuration */
#define ZIGBEE_LIGHT_ENDPOINT 10
uint8_t Relay_Signal = 23;
uint8_t button = BOOT_PIN;
uint8_t switchOnOff = 20;
uint8_t pairingButton = 21;
uint8_t indicatorLED = 22;

bool last_switch_state= false ;
bool pairingDone = false;

ZigbeeLight zbLight = ZigbeeLight(ZIGBEE_LIGHT_ENDPOINT);

// LED indicator mode enum
enum LedMode {
  LED_OFF,
  LED_ON,
  LED_BLINK_SLOW,
  LED_BLINK_FAST
};

LedMode currentLedMode = LED_BLINK_SLOW;



/********************* Relay_Signal functions **************************/
void setRelay(bool value) {
  digitalWrite(Relay_Signal, value);
  Serial.print("Zigbee command received: ");
  Serial.println(value ? "ON" : "OFF");
}


// Blink logic for status LED
void updateLedBlink() {
  static unsigned long lastBlink = 0;
  static bool ledState = false;
  unsigned long now = millis();

  int interval = 1000;
  if (currentLedMode == LED_BLINK_FAST) interval = 200;
  else if (currentLedMode == LED_BLINK_SLOW) interval = 1000;

  switch (currentLedMode) {
    case LED_ON:
      digitalWrite(indicatorLED, HIGH);
      break;
    case LED_OFF:
      digitalWrite(indicatorLED, LOW);
      break;
    case LED_BLINK_SLOW:
      if (now - lastBlink >= interval) {
          ledState = !ledState;
          digitalWrite(indicatorLED, ledState);
          lastBlink = now;
        }
        break;
    case LED_BLINK_FAST:
      if (now - lastBlink >= interval) {
        ledState = !ledState;
        digitalWrite(indicatorLED, ledState);
        lastBlink = now;
      }
      break;
  }
}




/********************* Arduino functions **************************/
void setup() {
  Serial.begin(115200);

  // Init Relay_Signal and turn it OFF (if Relay_Signal_PIN == RGB_BUILTIN, the rgbRelay_SignalWrite() will be used under the hood)
  pinMode(Relay_Signal, OUTPUT);
  digitalWrite(Relay_Signal, LOW);

  // Initialize modes 
  pinMode(button, INPUT);
  pinMode(switchOnOff, INPUT);
  pinMode(pairingButton, INPUT);
  pinMode(indicatorLED, OUTPUT);
  digitalWrite(indicatorLED, LOW);


  //Optional: set Zigbee device name and model
  zbLight.setManufacturerAndModel("Espressif", "ZBInWall");

  // Set callback function for light change
  zbLight.onLightChange(setRelay);

  //Add endpoint to Zigbee Core
  Serial.println("Adding ZigbeeLight endpoint to Zigbee Core");
  Zigbee.addEndpoint(&zbLight);

  // When all EPs are registered, start Zigbee. By default acts as ZIGBEE_END_DEVICE
  if (!Zigbee.begin()) {
    Serial.println("Zigbee failed to start!");
    currentLedMode = LED_OFF ;
    updateLedBlink() ;
    Serial.println("Rebooting...");
    ESP.restart();
  }

  Serial.println("Connecting to network");
  while (!Zigbee.connected()) {
    Serial.print(".");
    delay(100);
    updateLedBlink() ;
  }
  Serial.println();
  //currentLedMode = LED_ON;
}

void loop() {
  // Checking button for factory reset
  if (digitalRead(button) == LOW) {  // Push button pressed
    // Key debounce handling
    delay(100);
    int startTime = millis();
    while (digitalRead(button) == LOW) {
      delay(50);
      if ((millis() - startTime) > 3000) {
        // If key pressed for more than 3secs, factory reset Zigbee and reboot
        Serial.println("Resetting Zigbee to factory and rebooting in 1s.");
        delay(1000);
        Zigbee.factoryReset();
      }
    }
  }

  /* Pairing button logic
  if ((!pairingDone) && (digitalRead(pairingButton) == LOW)) {
    delay(100);
    unsigned long pressStart = millis();
    while (digitalRead(pairingButton) == LOW) {
      if (millis() - pressStart > 3000) {
        Serial.println("Entering pairing mode...");
        currentLedMode = LED_BLINK_FAST;
        pairingDone = true;
        Zigbee.factoryReset();
        break;
      }
      delay(50);
    }
  }*/


  // Switch state logic
  bool current_switch_state = (digitalRead(switchOnOff) == HIGH);
  if (current_switch_state != last_switch_state) {
    last_switch_state = current_switch_state;
    zbLight.setLight(current_switch_state);
    zbLight.setLight(zbLight.getLightState());
  }

  // If connected to Zigbee, set LED ON
  if (Zigbee.connected()) {
    currentLedMode = LED_ON;
  }
  else{
    currentLedMode = LED_BLINK_SLOW ;
  }


  updateLedBlink() ;
  delay(100);
}
