/*
  Adapted from the Inkplate10 examples
  https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Projects/Inkplate10_Image_Frame_From_Web/Inkplate10_Image_Frame_From_Web.ino and
  https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Advanced/Other/Inkplate10_Read_Battery_Voltage/Inkplate10_Read_Battery_Voltage.ino and
  https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Advanced/DeepSleep/Inkplate10_Wake_Up_Button/Inkplate10_Wake_Up_Button.ino

  What this code does:
    1. Connect to a WiFi access point
    2. Retrieve an image from a web address
    3. Display the image on the Inkplate 10 device
    4. Check the battery level on the Inkplate device
    5. Set a sleep timer for 60 minutes, and allow the Inkplate to go into deep sleep to conserve battery
*/

// Next 3 lines are a precaution, you can ignore those, and the example would also work without them
#if !defined(ARDUINO_INKPLATE10) && !defined(ARDUINO_INKPLATE10V2)
#error "Wrong board selection for this example, please select e-radionica Inkplate10 or Soldered Inkplate10 in the boards menu."
#endif

#include "Inkplate.h"

Inkplate display(INKPLATE_3BIT);

const char ssid[] = "YOUR WIFI SSID";  // Your WiFi SSID
const char *password = "YOUR WIFI PASSWORD";  // Your WiFi password
const char *imgurl = "http://url.to.your.server/image";  // Your dashboard image web address

#define BATTV_MAX 4.1  // maximum voltage of battery
#define BATTV_MIN 3.2  // what we regard as an empty battery
#define BATTV_LOW 3.4  // voltage considered to be low battery

void setup()
{
    Serial.begin(115200);
    display.begin();

    // Join wifi
    display.connectWiFi(ssid, password);

    displayInfo();

    // Go to sleep for 60min (60min * 60s * 1000ms * 1000us)
    esp_sleep_enable_timer_wakeup(60ll * 60 * 1000 * 1000);

    // Enable wakeup from deep sleep on gpio 36 (wake button)
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_36, LOW);

    // Go to sleep
    esp_deep_sleep_start();
}

void loop()
{
    // Never here! If you use deep sleep, the whole program should be in setup() because the board restarts each
    // time. loop() must be empty!
}

void displayInfo()
{
    // First, lets delete everything from frame buffer
    display.clearDisplay();

    // Display image from API
    if (!display.drawImage(imgurl, display.PNG, 0, 0))
    {
        // If is something failed (wrong filename or format), write error message on the screen.
        display.println("Image open error");
    }

    double battvoltage = display.readBattery();
    int battpc = calc_battery_percentage(battvoltage);
    if (battvoltage < BATTV_LOW) {
        char msg [20];
        sprintf (msg, "Battery: %d%%", battpc); 
        display.setCursor(1100, 800);  // Inkplate 10 has a 9.7 inch, 1,200 x 825 pixel display
        display.setTextSize(2);
        display.setTextColor(BLACK);
        display.print(msg);
    }

    display.display();  // Send everything to display (refresh the screen)
}


int calc_battery_percentage(double battv)
{    
    int battery_percentage = (uint8_t)(((battv - BATTV_MIN) / (BATTV_MAX - BATTV_MIN)) * 100);

    if (battery_percentage < 0)
        battery_percentage = 0;
    if (battery_percentage > 100)
        battery_percentage = 100;

    return battery_percentage;
}
