
#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include <ctype.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// =====================================================
// X/Z stepper control + DC motor
// Arduino Mega + Adafruit Motor Shield V2
// =====================================================

const int X_STEPS_PER_REV = 200;
const int Z_STEPS_PER_REV = 200;

const int MAX_SPEED = 400;
const long MAX_MOVE_STEPS = 10000;

const int DC_IN1 = 22;
const int DC_IN2 = 23;

const unsigned long SERIAL_BAUD = 115200;
const size_t BUFFER_SIZE = 100;

Adafruit_MotorShield shield = Adafruit_MotorShield(0x61);

Adafruit_StepperMotor *motorX =
    shield.getStepper(X_STEPS_PER_REV, 1);

Adafruit_StepperMotor *motorZ =
    shield.getStepper(Z_STEPS_PER_REV, 2);

char lineBuffer[BUFFER_SIZE];
size_t lineLength = 0;

bool moving = false;
bool stopRequested = false;
char activeAxis = '-';

// DC motor direction: 0 = stopped, 1 = forward, -1 = reverse
int dcDirection = 0;

// -----------------------------------------------------
// DC motor control
// -----------------------------------------------------

void stopDC() {
  digitalWrite(DC_IN1, LOW);
  digitalWrite(DC_IN2, LOW);
  dcDirection = 0;
  Serial.println(F("DC STOPPED"));
}

void setDCForward() {
  digitalWrite(DC_IN1, HIGH);
  digitalWrite(DC_IN2, LOW);
  dcDirection = 1;
  Serial.println(F("DC FORWARD"));
}

void setDCReverse() {
  digitalWrite(DC_IN1, LOW);
  digitalWrite(DC_IN2, HIGH);
  dcDirection = -1;
  Serial.println(F("DC REVERSE"));
}

// -----------------------------------------------------
// Serial input
// -----------------------------------------------------

bool readLine(char *output, size_t outputSize) {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\r') continue;

    if (c == '\n') {
      lineBuffer[lineLength] = '\0';

      strncpy(output, lineBuffer, outputSize - 1);
      output[outputSize - 1] = '\0';

      lineLength = 0;
      return true;
    }

    if (lineLength < BUFFER_SIZE - 1) {
      lineBuffer[lineLength++] = c;
    } else {
      lineLength = 0;
      Serial.println(F("ERROR command too long"));
    }
  }

  return false;
}

void printStatus() {
  Serial.print(F("STATUS "));
  Serial.print(moving ? F("MOVING ") : F("IDLE "));
  Serial.print(activeAxis);
  Serial.print(F(" DC "));

  if (dcDirection == 1) {
    Serial.println(F("FORWARD"));
  } else if (dcDirection == -1) {
    Serial.println(F("REVERSE"));
  } else {
    Serial.println(F("STOPPED"));
  }
}

// -----------------------------------------------------
// Command processing
// -----------------------------------------------------

void handleCommand(char *line);

void serviceSerialDuringMove() {
  char incoming[BUFFER_SIZE];

  while (readLine(incoming, sizeof(incoming))) {
    handleCommand(incoming);
  }
}

void moveAxis(char axis, long steps, int speedStepsPerSec) {
  if (axis != 'X' && axis != 'Z') {
    Serial.println(F("ERROR invalid axis"));
    return;
  }

  if (steps == 0 || labs(steps) > MAX_MOVE_STEPS) {
    Serial.println(F("ERROR invalid step count"));
    return;
  }

  if (speedStepsPerSec < 1 ||
      speedStepsPerSec > MAX_SPEED) {
    Serial.println(F("ERROR invalid speed"));
    return;
  }

  Adafruit_StepperMotor *motor =
      (axis == 'X') ? motorX : motorZ;

  int stepsPerRev =
      (axis == 'X') ? X_STEPS_PER_REV : Z_STEPS_PER_REV;

  int rpm = (int)(
      ((long)speedStepsPerSec * 60L + stepsPerRev / 2)
      / stepsPerRev
  );

  if (rpm < 1) rpm = 1;

  motor->setSpeed(rpm);

  uint32_t remaining = (uint32_t)labs(steps);
  uint8_t direction = (steps > 0) ? FORWARD : BACKWARD;

  moving = true;
  stopRequested = false;
  activeAxis = axis;

  Serial.print(F("MOVING "));
  Serial.println(axis);

  while (remaining > 0 && !stopRequested) {
    serviceSerialDuringMove();

    if (stopRequested) break;

    motor->step(1, direction, INTERLEAVE);
    remaining--;
  }

  motor->release();

  moving = false;

  if (stopRequested) {
    Serial.print(F("STOPPED "));
    Serial.println(axis);
  } else {
    Serial.print(F("DONE "));
    Serial.println(axis);
  }

  activeAxis = '-';
}

void handleCommand(char *line) {
  while (*line && isspace((unsigned char)*line)) {
    line++;
  }

  if (*line == '\0') return;

  // Global stop: stop the active stepper and DC motor.
  if (strcasecmp(line, "STOP") == 0) {
    stopRequested = true;
    stopDC();
    Serial.println(F("OK stop requested"));
    return;
  }

  if (strcasecmp(line, "STATUS") == 0) {
    printStatus();
    return;
  }

  // DC commands
  if (strcasecmp(line, "DC FORWARD") == 0) {
    setDCForward();
    return;
  }

  if (strcasecmp(line, "DC REVERSE") == 0) {
    setDCReverse();
    return;
  }

  if (strcasecmp(line, "DC STOP") == 0) {
    stopDC();
    return;
  }

  // Stepper command: MOVE X <steps> <speed>
  char command[12] = {0};
  char axis = '\0';
  long steps = 0;
  int speed = 0;
  char extra = '\0';

  int fields = sscanf(
      line, "%11s %c %ld %d %c",
      command, &axis, &steps, &speed, &extra
  );

  if (strcasecmp(command, "MOVE") == 0 && fields == 4) {
    axis = (char)toupper((unsigned char)axis);

    if (moving) {
      Serial.println(F("ERROR BUSY"));
      return;
    }

    moveAxis(axis, steps, speed);
    return;
  }

  Serial.println(F("ERROR unknown command"));
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Wire.begin();

  pinMode(DC_IN1, OUTPUT);
  pinMode(DC_IN2, OUTPUT);
  stopDC();

  if (!shield.begin()) {
    Serial.println(F("ERROR motor shield not detected"));
    while (true) delay(1000);
  }

  motorX->release();
  motorZ->release();

  Serial.println(F("READY X/Z/DC controller"));
}

void loop() {
  char command[BUFFER_SIZE];

  if (readLine(command, sizeof(command))) {
    handleCommand(command);
  }
}
