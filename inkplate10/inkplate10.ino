/*
  Inkplate 10 client for this repository's dashboard server: connect to WiFi, download the
  rendered image, draw it in greyscale, warn about a low battery, go back to deep sleep.

  Adapted from the Inkplate 10 examples of the Inkplate Arduino library:
  https://github.com/SolderedElectronics/Inkplate-Arduino-library/tree/master/examples/Inkplate10
*/

#if !defined(ARDUINO_INKPLATE10) && !defined(ARDUINO_INKPLATE10V2)
#error "Wrong board selection, please select e-radionica Inkplate10 or Soldered Inkplate10 in the boards menu."
#endif

#include "HTTPClient.h"
#include "Inkplate.h"
#include "WiFi.h"

// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// The server serves a 1200x825 PNG at /image on port 5000. Works with https:// too, but
// then the server certificate is not verified.
const char* IMG_URL = "https://url-to-your-server/image";

// Rendering the image starts a headless browser, so answers can take a while
#define WIFI_TIMEOUT_MS 30000
#define HTTP_CONNECT_TIMEOUT_MS 15000
#define HTTP_READ_TIMEOUT_MS 30000
#define DOWNLOAD_TIMEOUT_MS 120000
#define MAX_DOWNLOAD_ATTEMPTS 3
#define RETRY_DELAY_MS 5000

#define BATTV_MAX 4.1  // maximum voltage of battery
#define BATTV_MIN 3.2  // what we regard as an empty battery
#define BATTV_LOW 3.4  // voltage considered to be low battery

#define SLEEP_MINUTES 60

Inkplate display(INKPLATE_1BIT);

// Appends to the boot log, which is never overwritten: text has a transparent background,
// so printing spaces does not erase anything.
void printStatus(const String& text) {
    display.print(text);
    display.partialUpdate();
}

// A newline resets x to 0, so every boot log line needs its cursor placed explicitly
void statusLine(int line) {
    display.setCursor(25, 25 + line * 25);
}

bool connectToWiFi() {
    WiFi.persistent(false);
    WiFi.mode(WIFI_MODE_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    statusLine(0);
    printStatus("Connecting to WiFi");

    uint8_t dots = 0;
    uint32_t startAttemptTime = millis();
    uint32_t lastDot = startAttemptTime;
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_TIMEOUT_MS) {
        delay(500);
        if (millis() - lastDot >= 2000) {
            lastDot = millis();
            if (dots++ < 30) printStatus(".");
        }
    }

    bool connected = WiFi.status() == WL_CONNECTED;
    if (connected) {
        Serial.printf("WiFi connected, IP %s, RSSI %d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
        printStatus(" Successful.");
    } else {
        Serial.printf("WiFi connection failed, status %d\n", (int)WiFi.status());
        printStatus(" Failed.");
    }
    return connected;
}

// Downloads IMG_URL into a buffer, which the caller owns and has to free on success
bool downloadImage(uint8_t** buffer, int32_t* length) {
    HTTPClient http;
    http.setConnectTimeout(HTTP_CONNECT_TIMEOUT_MS);
    http.setTimeout(HTTP_READ_TIMEOUT_MS);  // the core takes a uint16_t here

    if (!http.begin(IMG_URL)) {
        Serial.println("HTTP: invalid image URL");
        return false;
    }

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("HTTP: request failed with code %d\n", httpCode);
        return false;
    }

    int32_t size = http.getSize();
    if (size <= 0) {
        Serial.println("HTTP: response has no content length");
        return false;
    }

    uint8_t* image = (uint8_t*)ps_malloc(size);
    if (image == nullptr) image = (uint8_t*)malloc(size);
    if (image == nullptr) {
        Serial.printf("HTTP: out of memory for %d bytes\n", (int)size);
        return false;
    }

    auto* stream = http.getStreamPtr();
    uint8_t chunk[512];
    int32_t received = 0;
    uint32_t deadline = millis() + DOWNLOAD_TIMEOUT_MS;

    while (received < size && (int32_t)(millis() - deadline) < 0) {
        size_t available = stream->available();
        if (available == 0) {
            delay(1);
            continue;
        }

        // Clamp to the space that is left, a wrong content length would overrun the buffer
        size_t wanted = available < sizeof(chunk) ? available : sizeof(chunk);
        if (wanted > (size_t)(size - received)) wanted = size - received;

        int readCount = stream->readBytes(chunk, wanted);
        if (readCount <= 0) break;  // timed out, or the connection closed too early

        memcpy(image + received, chunk, readCount);
        received += readCount;
    }

    if (received != size) {
        Serial.printf("HTTP: received %d of %d bytes\n", (int)received, (int)size);
        free(image);
        return false;
    }

    *buffer = image;
    *length = size;
    return true;
}

bool downloadAndDrawImage() {
    statusLine(1);
    printStatus("Downloading image...");

    int row = 2;
    for (int attempt = 1; attempt <= MAX_DOWNLOAD_ATTEMPTS; attempt++) {
        if (attempt > 1) {
            display.selectDisplayMode(INKPLATE_1BIT);  // partial updates stop in greyscale
            statusLine(row++);
            printStatus("Retrying download " + String(attempt) + "/" + String(MAX_DOWNLOAD_ATTEMPTS) + "...");
            delay(RETRY_DELAY_MS);
        }

        uint8_t* buffer = nullptr;
        int32_t size = 0;
        if (!downloadImage(&buffer, &size)) continue;

        display.selectDisplayMode(INKPLATE_3BIT);
        display.clearDisplay();

        bool drawn = display.image.drawPngFromBuffer(buffer, size, 0, 0, true, false);
        free(buffer);  // drawPngFromBuffer does not free the buffer
        if (drawn) return true;

        Serial.println("PNG: decoding the image failed");
    }
    return false;
}

// Only drawn when the battery is low, but always logged over the serial port
void displayBatteryStatus() {
    double battvoltage = 0;
    for (int i = 0; i < 5; i++) {  // the battery ADC is noisy, so average a few readings
        battvoltage += display.readBattery();
        delay(10);
    }
    battvoltage /= 5;

    double percentage = ((battvoltage - BATTV_MIN) / (BATTV_MAX - BATTV_MIN)) * 100;
    if (percentage < 0) percentage = 0;
    if (percentage > 100) percentage = 100;
    int battpc = (int)percentage;

    Serial.printf("Battery: %d mV, %d%%\n", (int)(battvoltage * 1000), battpc);
    if (battvoltage < BATTV_LOW) {
        display.setCursor(1025, 800);  // bottom right of the 1,200 x 825 screen
        display.println("Battery: " + String(battpc) + "%");
    }
}

void setup() {
    Serial.begin(115200);
    Serial.printf("\nBoot, wakeup cause %d\n", (int)esp_sleep_get_wakeup_cause());

    display.begin();
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(BLACK);

    bool imageShown = false;
    if (connectToWiFi()) imageShown = downloadAndDrawImage();

    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);

    if (imageShown) {
        displayBatteryStatus();
    } else {
        display.selectDisplayMode(INKPLATE_1BIT);
        display.clearDisplay();
        statusLine(0);
        printStatus("Could not update the dashboard.");
        statusLine(1);
        printStatus("Check the server and the WiFi.");
        displayBatteryStatus();
    }

    display.display();

    Serial.printf("Sleeping for %d minutes\n", SLEEP_MINUTES);
    Serial.flush();
    esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_MINUTES * 60ULL * 1000000ULL);
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_36, LOW);  // gpio 36 is the wake button
    esp_deep_sleep_start();
}

void loop() {
    // Never here, deep sleep restarts the board on every wake-up
}
