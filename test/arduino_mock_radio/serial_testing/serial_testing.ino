
int TEAM_ID = 1071;
String MISSION_TIME = "12:12:12.56";
int PACKET_COUNT = 0;
char MODE = 'F';
String STATE = "LAUNCH_WAIT";
double ALTITUDE = 0;
char HS_DEPLOYED = 'M';
char PC_DEPLOYED = 'D';
char MAST_RAISED = 'M';
double TEMPERATURE = 25.0;
double VOLTAGE = 5.5;
double PRESSURE = 100;
String GPS_TIME = "12:12:12.56";
double GPS_ALTITUDE = 160;
double GPS_LATITUDE = 29.6446;
double GPS_LONGITUDE = -82.3535;
int GPS_SATS = 14;
double TILT_X = 50;
double TILT_Y = 50;
bool cont = false;
void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:


if (Serial.available() > 0){
  String comm = Serial.readString();
  
  if (comm == "CMD,1071,CX,ON\n"){
    cont = true; 
  }
  else if (comm == "CMD,1071,CX,OFF\n"){
    cont = false;
  }
}

// if (cont == false) return;

if (PACKET_COUNT > 600){
  PACKET_COUNT = 1;
  ALTITUDE = 1;
}
else if (PACKET_COUNT > 300){
  PACKET_COUNT ++;
  ALTITUDE -= 2;
  GPS_ALTITUDE -= 2;
  GPS_LATITUDE -= 0.09;
  GPS_LONGITUDE -= 0.005;
  TEMPERATURE -= 0.01;
  TILT_X -= 0.1;
  TILT_Y -= 0.1;
  VOLTAGE -= 0.001;
}
else{
  PACKET_COUNT ++;
  ALTITUDE += 2;
  GPS_ALTITUDE += 2;
  GPS_LATITUDE += 0.007;
  GPS_LONGITUDE += 0.003;
  TEMPERATURE += 0.01;
  TILT_X += 0.1;
  TILT_Y += 0.1;
  VOLTAGE += 0.001;
}



String command_to_send = "";
command_to_send += String(TEAM_ID);
command_to_send += ",";
command_to_send += MISSION_TIME;
command_to_send += ",";
command_to_send += String(PACKET_COUNT);
command_to_send += ",";
command_to_send += MODE;
command_to_send += ",";
command_to_send += STATE;
command_to_send += ",";
command_to_send += ALTITUDE;
command_to_send += ",";
command_to_send += HS_DEPLOYED;
command_to_send += ",";
command_to_send += PC_DEPLOYED;
command_to_send += ",";
command_to_send += TEMPERATURE;
command_to_send += ",";
command_to_send += VOLTAGE;
command_to_send += ",";
command_to_send += PRESSURE;
command_to_send += ",";
command_to_send += GPS_TIME;
command_to_send += ",";
command_to_send += GPS_ALTITUDE;
command_to_send += ",";
command_to_send += GPS_LATITUDE;
command_to_send += ",";
command_to_send += GPS_LONGITUDE;
command_to_send += ",";
command_to_send += GPS_SATS;
command_to_send += ",";
command_to_send += TILT_X;
command_to_send += ",";
command_to_send += TILT_Y;
Serial.println(command_to_send);
delay(1000);

}
