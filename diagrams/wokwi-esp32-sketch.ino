// Office Watch — one-room ESP32 node (representative circuit)
// -----------------------------------------------------------------------------
// Reads the ON/OFF state of one room's 5 devices (2 fans + 3 lights), mirrors
// each on an LED, reads the room's aggregate current, shows a live summary on an
// I2C LCD, and prints a JSON line (what a real node would POST to the backend).
//
// In a real build the sense inputs come from AC optocouplers and the current
// reading from an ACS712/CT clamp. In the Wokwi simulation:
//   - each sense input  <- a slide switch (switch = that device is energised)
//   - the current input <- a potentiometer (turn it = more room current)
//   - each mirror LED shows what is ON at a glance
//   - the I2C LCD shows total power + how many devices are on
//
// Pin map matches diagram.json and diagrams/circuit-guide.md.
//
// NOTE: Arduino sketch (C++). The file must end in .ino or .cpp -- NOT .c.
// -----------------------------------------------------------------------------
#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>   // Wokwi: add "LiquidCrystal I2C" in the Library Manager

const int   NUM_DEVICES   = 5;
const int   SENSE_PINS[5] = {13, 14, 23, 22, 18};   // Fan1, Fan2, Light1, Light2, Light3
const int   LED_PINS[5]   = {12, 27, 26, 25, 33};   // mirror LEDs
const char* LABELS[5]     = {"Fan 1", "Fan 2", "Light 1", "Light 2", "Light 3"};
const int   RATED_W[5]    = {60, 60, 15, 15, 15};   // rated watts per device
const int   CURRENT_PIN   = 34;                     // ADC1 (ADC2 clashes with Wi-Fi)
const int   ROOM_MAX_W    = 2 * 60 + 3 * 15;        // one room all-on = 165 W (sensor full-scale)

// On-board 16x2 I2C LCD (SDA=GPIO21, SCL=GPIO4; both free, any I2C pins work).
const int   I2C_SDA = 21;
const int   I2C_SCL = 4;
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_DEVICES; i++) {
    pinMode(SENSE_PINS[i], INPUT_PULLDOWN);  // defined LOW when a device is off
    pinMode(LED_PINS[i], OUTPUT);
  }
  Wire.begin(I2C_SDA, I2C_SCL);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Office Watch");
}

void loop() {
  int    estWatts = 0;
  int    onCount  = 0;
  String devices  = "";

  for (int i = 0; i < NUM_DEVICES; i++) {
    bool on = digitalRead(SENSE_PINS[i]) == HIGH;
    digitalWrite(LED_PINS[i], on ? HIGH : LOW);        // mirror state on the board
    if (on) { estWatts += RATED_W[i]; onCount++; }
    devices += String("\"") + LABELS[i] + "\":" + (on ? "true" : "false");
    if (i < NUM_DEVICES - 1) devices += ",";
  }

  // ACS712 / potentiometer -> 0..4095 -> plausible 0..165 W room current.
  int raw         = analogRead(CURRENT_PIN);
  int sensedWatts = map(raw, 0, 4095, 0, ROOM_MAX_W);

  // Live summary on the LCD (trailing spaces clear leftover digits).
  lcd.setCursor(0, 0);
  lcd.print("Power: ");
  lcd.print(estWatts);
  lcd.print("W    ");
  lcd.setCursor(0, 1);
  lcd.print("Devices: ");
  lcd.print(onCount);
  lcd.print("/");
  lcd.print(NUM_DEVICES);
  lcd.print(" ON ");

  // One JSON line = the payload a real node would POST to the backend /ingest
  // endpoint. (In this project the backend simulator produces this same shape.)
  Serial.print("{\"room\":\"work1\",\"devices\":{");
  Serial.print(devices);
  Serial.print("},\"estWatts\":");
  Serial.print(estWatts);
  Serial.print(",\"sensedWatts\":");
  Serial.print(sensedWatts);
  Serial.println("}");

  delay(1000);
}
