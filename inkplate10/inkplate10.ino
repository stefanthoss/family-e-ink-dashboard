/*
  Adapted from the Inkplate10 examples:
  * https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Advanced/WEB_WiFi/Inkplate10_Show_JPG_With_HTTPClient/Inkplate10_Show_JPG_With_HTTPClient.ino
  * https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Advanced/Other/Inkplate10_Read_Battery_Voltage/Inkplate10_Read_Battery_Voltage.ino
  * https://github.com/SolderedElectronics/Inkplate-Arduino-library/blob/2dd263f2f9548aadac8638413a143beddf068a64/examples/Inkplate10/Advanced/DeepSleep/Inkplate10_Wake_Up_Button/Inkplate10_Wake_Up_Button.ino

  What this code does:
    1. Connect to a WiFi access point
    2. Retrieve an image from a web address
    3. Display the image on the Inkplate 10 device
    4. Check the battery level on the Inkplate device
    5. Set a sleep timer for 60 minutes, and allow the Inkplate to go into deep sleep to conserve battery
*/

#if !defined(ARDUINO_INKPLATE10) && !defined(ARDUINO_INKPLATE10V2)
#error                                                                                                                 \
    "Wrong board selection for this example, please select e-radionica Inkplate10 or Soldered Inkplate10 in the boards menu."
#endif

#include "HTTPClient.h"
#include "Inkplate.h"
#include "WiFi.h"

#include "lib/png_image_helper.cpp"

char *ssid = "YOUR WIFI SSID";  // Your WiFi SSID
char *pass = "YOUR WIFI PASSWORD";  // Your WiFi password
String imgurl = "https://url.to.your.server/image";  // Your dashboard image web address

#define BATTV_MAX 4.1  // maximum voltage of battery
#define BATTV_MIN 3.2  // what we regard as an empty battery
#define BATTV_LOW 3.4  // voltage considered to be low battery

Inkplate display(INKPLATE_1BIT);

void setup()
{
    Serial.begin(115200);
    display.begin();             // Init Inkplate library
    display.clearDisplay();      // Clear frame buffer of display
    display.setTextSize(2);      // Set text size to be 2 times bigger than original (5x7 px)
    display.setTextColor(BLACK); // Set text color to black
    display.setCursor(25, 25);

    // Show a connection message
    display.print("Connecting to WiFi");
    display.partialUpdate();

    // Actually connect to the WiFi network
    WiFi.mode(WIFI_MODE_STA);
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        display.print(".");
        display.partialUpdate();
    }
    display.print(" Successful.");
    display.partialUpdate();
    display.setCursor(25, 50);
    display.print("Downloading image...");
    display.partialUpdate();

    // Switch to 3-bit mode so the image will be of better quality
    display.setDisplayMode(INKPLATE_3BIT);

    // Make an object for the HTTP client
    HTTPClient http;
    http.setTimeout(5000);
    http.begin(imgurl);

    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK)
    {
        // Get the size of the image
        int32_t size = http.getSize();
        int32_t len = size;

        if (size > 0)
        {
            // Allocate the memory for the image
            uint8_t *buffer = (uint8_t *)ps_malloc(size);
            uint8_t *buffPtr = buffer; // Copy of the buffer pointer so that the original one is not lost

            // Temporary buffer for retrieving parts of the image and storing them in the real buffer
            uint8_t buff[512] = {0};

            // Let's fetch the data
            WiFiClient *stream = http.getStreamPtr(); // We need a stream pointer to know how much data is available

            // Repeat as long as we have a connection and while there is data to read
            while (http.connected() && (len > 0 || len == -1))
            {
                // Get the number of available bytes
                size_t size = stream->available();

                // If there are available bytes, read them
                if (size)
                {
                    // Read available bytes from the stream and store them in the buffer
                    int c = stream->readBytes(buff, ((size > sizeof(buff)) ? sizeof(buff) : size));
                    memcpy(buffPtr, buff, c);

                    // As we read the data, we subtract the length we read and the remaining length is in the variable
                    // len
                    if (len > 0)
                        len -= c;

                    // Likewise for the buffer pointer
                    buffPtr += c;
                }
                else if (len == -1)
                {
                    len = 0;
                }
            }

            // Draw image into the frame buffer of Inkplate
            drawPngFromBuffer(buffer, size, 0, 0, true, false);
        }
        else
        {
            // Show an error message
            display.setCursor(25, 75);
            display.print("Invalid response length " + String(size) + " (HTTP " + String(httpCode) + ")");
        }
    }
    else
    {
        // Show an error message
        display.setCursor(25, 75);
        display.print("HTTP error " + String(httpCode));
    }

    // Show battery percentage if low
    double battvoltage = display.readBattery();
    int battpc = calc_battery_percentage(battvoltage);
    if (battvoltage < BATTV_LOW) {
        display.setCursor(1025, 800);  // Inkplate 10 has a 9.7 inch, 1,200 x 825 pixel display
        display.println("Battery: " + String(battpc) + "%");
    }

    // Draw image on the screen
    display.display();

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

int calc_battery_percentage(double battv)
{    
    int battery_percentage = (uint8_t)(((battv - BATTV_MIN) / (BATTV_MAX - BATTV_MIN)) * 100);

    if (battery_percentage < 0)
        battery_percentage = 0;
    if (battery_percentage > 100)
        battery_percentage = 100;

    return battery_percentage;
}
