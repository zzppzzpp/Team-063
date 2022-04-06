#define DIR_PIN 2
#define STEP_PIN 3
#define EN_PIN 4
#define LIMIT 7
#define SCAN_STEPS 400
#define ENC_TO_DEG 0.3515625

int runFlag = 1;
int stepSpeed = 20;
int stepSpeedSlow = 100;
//int encoderBuffer[14000];

long revolutions = 0;   // number of revolutions the encoder has made
double position = 0;    // the calculated value the encoder is at
double output;          // raw value from AS5600
long lastOutput;        // last output from AS5600

String encoderValues = "[";
String dataPkg = "";

void setup() {
  Serial.begin(250000);
  
  // Declare pins as output:
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  pinMode(13, OUTPUT);
  pinMode(LIMIT, INPUT_PULLUP);
  
  // Set the spinning direction CW/CCW:
  digitalWrite(DIR_PIN, HIGH);

}
void loop() {

  int cmd = listenToPort();
  switch (cmd) {
    case 'A':
      scan();
      break;
    // Toggle gantry forward
    case 'F':
      spin(3000, 1);
      break;
    // Toggle gantry backward
    case 'B':
      spin(3000, 0);
      break;
    // Stop gantry movement
    case 'S':
      stopMotor();
      break;

      // Stop gantry movement
    case 'W':
      stepSpeed = 50;
      break;

    // Stop gantry movement
    case 'Q':
      stepSpeed = 100;
      break;
    // Home the gantry
    case 'R':
      spin(16000, 0);
      break;

    default:
      stopMotor();
      break;
  }
}

void spin(int steps, int dir) {
  startMotor();
  
  if (dir) digitalWrite(DIR_PIN, HIGH);
  else digitalWrite(DIR_PIN, LOW);

  for (int i = 0; i < steps; i++) {

    if (digitalRead(LIMIT)) {
      break;  
    }
    
    // read analog sensor and send to python gui
    int output = analogRead(A5);
    
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepSpeed);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepSpeed);
  }
  if (digitalRead(LIMIT)) {
      spinNoLimit(1000, 1);
  }
  stopMotor();
}


void spinAndRecord(int steps, int dir) {
  startMotor();
  
  if (dir) digitalWrite(DIR_PIN, HIGH);
  else digitalWrite(DIR_PIN, LOW);

  for (int i = 0; i < steps; i++) {

    // read analog sensor and send to python gui
    int currentAngle = getRotorPosition();
    // This sends both the encoder and sensor data as a formatted package to the Python gui
    dataPkg = String(currentAngle) + "," + String(analogRead(A0));
    Serial.println(dataPkg);

    if (listenToPort() == 'P') {
      break;
    }
        
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepSpeed);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepSpeed);
  }
  stopMotor();

  // Format encoder values to send over serial
  int lastIndex = encoderValues.length() - 1;
  encoderValues.remove(lastIndex);
  encoderValues += "]";
  //Serial.println(encoderValues);
  encoderValues = "[";
  
}

void scan() {
   spinAndRecord(14000, 1);
   Serial.println("STOP");

}

void stopMotor() {
    digitalWrite(EN_PIN, HIGH);
}

void startMotor() {
    digitalWrite(EN_PIN, LOW);
}

int listenToPort() {
  int incomingByte;
  if (Serial.available() > 0) {
    incomingByte = Serial.read();
    return incomingByte;
  }
}

int getRotorPosition() {
  output = analogRead(A5);           // get the raw value of the encoder                      
  
  if ((lastOutput - output) > 511 )        // check if a full rotation has been made
    revolutions++;
  if ((lastOutput - output) < -511 )
    revolutions--;
    
  position = revolutions * 1024 + output;   // calculate the position the the encoder is at based off of the number of revolutions

  lastOutput = output;  

  return position;
}

void spinNoLimit(int steps, int dir) {
  startMotor();
  
  if (dir) digitalWrite(DIR_PIN, HIGH);
  else digitalWrite(DIR_PIN, LOW);

  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepSpeed);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepSpeed);
  }
  stopMotor();
}
