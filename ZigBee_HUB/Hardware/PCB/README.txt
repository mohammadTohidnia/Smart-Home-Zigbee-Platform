This is the final version of Zigbee HUB with Orange PI. The features:
1. It is designed in a way that can be used as HUB or Router. If you use HUB, Do not assemble Regulator components. 
If you want Router, you have to assemble the AMS1117 regulator.

2. It has some pin headers for future developments (I2C and SPI of CC2652P4I)

3. It needs a 5V/2A or 5V/3A adaptor to power the board.

4. If you see a voltage drop, you can short circuit the schottky diode.

5. In new version, the LEDs are smd and they need a LENZ to make the light better and straight.

6. If you hold the reset button for more than 3 secs, you put the hub into pairing mode and it allows devices to join the network.