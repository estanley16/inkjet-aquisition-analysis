
#include <Servo.h>

Servo myservo;  // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 0;

void setup() {
  // put your setup code here, to run once:
  myservo.attach(9);  // attaches the servo on pin 9 to the servo object
  Serial.begin(9600);
}

void loop() {

  // put your main code here, to run repeatedly:
  // send data only when you receive data:
  if (Serial.available() > 0) {
    char x = Serial.read();

    if (x == 'z') {
      for (pos = 80; pos <= 140; pos += 2) {
        myservo.write(pos);              // tell servo to go to position in variable 'pos'
        delay(50); 
        //Serial.println(pos);
      }
      Serial.println("c");
    }
   
      else if (x == 'a') {
        for (pos = 140; pos >= 80; pos -= 2) {
          myservo.write(pos);              // tell servo to go to position in variable 'pos'
          delay(50); 
          //Serial.println(pos);
        }
        Serial.println("o");
      }

    }

  }
