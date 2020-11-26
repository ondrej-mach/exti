#include <AccelStepper.h>
#include <Adafruit_NeoPixel.h>

#define en 8
#define Lstep 11
#define Ldir 12
#define Rstep 9
#define Rdir 10

#define echo 2
#define trig 3

#define fan 7
#define button 4
#define neopixel 13

#define Rline A0
#define Lline A1

#define Rtouch A2
#define Ltouch A3

#define IRsensor A4


#define go_acceleration 1600
#define turn_acceleration 700

#define maxSpeed 550
#define stepsPerDegree 2.7
#define stepsPerCm 17


AccelStepper Lmotor(1, Lstep, Ldir);
AccelStepper Rmotor(1, Rstep, Rdir);

Adafruit_NeoPixel pixels(16, neopixel, NEO_GRB + NEO_KHZ800);

byte brightness = 128;

const bool color[8][3] = {
    {1,0,0},
    {0,1,0},
    {0,0,1},
    {0,1,1},
    {1,0,1},
    {1,1,0},
    {1,1,1},
    {0,0,0},
};

bool motorBusy;
byte distance = 255;

bool halt = false;
bool touch = false;
bool LT = false;
bool RT = false;
bool LL = false;
bool RL = false;


bool rightTouch(){
    bool value = RT;
    RT = false;
    return value;
}

bool leftTouch(){
    bool value = LT;
    LT = false;
    return value;
}

bool rightLine(){
    bool value = RL;
    RL = false;
    return value;
}

bool leftLine(){
    bool value = LL;
    LL = false;
    return value;
}

bool fire(){
    return !digitalRead(IRsensor);
}

void enable(){
    digitalWrite(en, LOW);
}

void disable(){
    digitalWrite(en, HIGH);
}

void stop(){
    Lmotor.move(0);
    Rmotor.move(0);
}

void go(int distance){
    Lmotor.setAcceleration(go_acceleration);
    Rmotor.setAcceleration(go_acceleration);
    Lmotor.move(distance * stepsPerCm);
    Rmotor.move(distance * stepsPerCm);
}

void turn(int angle){
    Lmotor.setAcceleration(turn_acceleration);
    Rmotor.setAcceleration(turn_acceleration);
    Lmotor.move(-angle * stepsPerDegree);
    Rmotor.move(angle * stepsPerDegree);
}

void changeLed(int mode){
    pixels.clear();
    for(int i=0; i<16; i++)
        pixels.setPixelColor(i, pixels.Color(color[mode][0]*brightness, color[mode][1]*brightness, color[mode][2]*brightness));
    pixels.show();
}

void runMotors(){
    if(Lmotor.distanceToGo() == 0 and Rmotor.distanceToGo() == 0){
        disable();
        motorBusy = 0;
    }
    else{
        enable();
        motorBusy = 1;
    }
    
    Lmotor.run();
    Rmotor.run();
}

void setup(){
    disable();
    
    Lmotor.setMaxSpeed(maxSpeed);
    Rmotor.setMaxSpeed(maxSpeed);

    pinMode(en, OUTPUT);
    pinMode(Lstep, OUTPUT);
    pinMode(Ldir, OUTPUT);
    pinMode(Rstep, OUTPUT);
    pinMode(Rdir, OUTPUT);

    pinMode(fan, OUTPUT);
    pinMode(button, INPUT_PULLUP);
    
    pinMode(IRsensor, INPUT);
    pinMode(Rtouch, INPUT_PULLUP);
    pinMode(Ltouch, INPUT_PULLUP);
    pinMode(Rline, INPUT);
    pinMode(Lline, INPUT);

    pinMode(echo, INPUT);
    pinMode(trig, OUTPUT);

    digitalWrite(fan, HIGH);
    
    Serial.begin(115200);
    pixels.begin();
    changeLed(7);

    attachInterrupt(digitalPinToInterrupt(echo), echoChange, CHANGE);
}


void loop(){
    communicate();
    runMotors();
    sendTrig();
    checkSensors();
}

byte waitSerial(){
    while(!Serial.available()){
        Lmotor.run();
        Rmotor.run();
    }
    delay(1);
    return(Serial.read());
}

void communicate(){
    while(Serial.available()){
        char rc = Serial.read();
        char instruction = rc;

        char number[5] = {'\0','\0','\0','\0','\0'};
        int i = 0;
        do{
            rc = waitSerial();
            number[i] = rc;
            i++;
        }while(rc != '\n' and i < 5);
        
        int argument = atoi(number);

        switch(instruction){
            case 'F':
                digitalWrite(fan, !argument);
                break;

            case 'T':
                turn(argument);
                break;

            case 'D':
                go(argument);
                break;

            case 'L':
                changeLed(argument);
                break;

            case 'S':
                serialSend();
                break;
        }
    }
}


void checkSensors(){
    static uint64_t buttonStart;
    static bool holding;
    static bool halting;
    
    if(digitalRead(button) == 0){
        if(holding){
            if((buttonStart + 2000 < millis()) and !halting){
                halt = true;
                halting = true;
            }
        }else{
            holding = true;
            buttonStart = millis();
        }
    }else{
        if(holding){
            touch = true;
            holding = false;
        }
        halting = false;  
    }

    LT = LT or !digitalRead(Ltouch);
    RT = RT or !digitalRead(Rtouch);
    LL = LL or digitalRead(Lline);
    RL = RL or digitalRead(Rline);
}

void serialSend(){
    byte outByte = 0;
    outByte = outByte | ((1<<0) * fire());
    outByte = outByte | ((1<<1) * leftTouch());
    outByte = outByte | ((1<<2) * rightTouch());
    outByte = outByte | ((1<<3) * leftLine());
    outByte = outByte | ((1<<4) * rightLine());

    Serial.write(outByte);

    outByte = 0;
    outByte = outByte | ((1<<0) * motorBusy);
    outByte = outByte | ((1<<1) * buttonTouched());
    outByte = outByte | ((1<<2) * halted());
    Serial.write(outByte);

    outByte = distance;
    Serial.write(outByte);
}

void echoChange(){
    static uint64_t echoStart;
    if(digitalRead(echo) == HIGH){
        echoStart = micros();
    }else{
        float d = micros() - echoStart;
        d /= 58;
        distance = constrain(d, 0, 255);
    }
}

void sendTrig(){
    static uint64_t lastTrig;
    if(lastTrig + 60 < millis()){
        digitalWrite(trig, HIGH);
        delayMicroseconds(10); 
        digitalWrite(trig, LOW);
        lastTrig = millis();
    }
}

bool halted(){
    if(halt){
        halt = false;
        return true;
    }
    return false;
}

bool buttonTouched(){
        if(touch){
        touch = false;
        return true;
    }
    return false;
}
