#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <time.h>
#include <WiFiClientSecureBearSSL.h>
#include <math.h>  // powf, logf

// ====== 사용자 설정 ======
#define WIFI_SSID      "eunhye"
#define WIFI_PASS      "01092011558"

#define MQTT_HOST      "l9cc66c2.ala.asia-southeast1.emqxsl.com"
#define MQTT_PORT      8883
#define MQTT_USER      "esp8266"
#define MQTT_PASS      "qwer1234"

#define DEVICE_ID      "1"
#define TOPIC_TEL      "pland/soil/humid/telemetry"
#define TOPIC_STATUS   "pland/soil/humid/status"

// 센서 보정값
int RAW_DRY = 1023;   // 건조한 토양에서 읽은 값
int RAW_WET = 0;   // 충분히 젖은 토양에서 읽은 값

// 딥슬립 주기
const int DEEP_SLEEP_MINUTES = 55;

// 감마 보정 기준점 
const int   CAL_ANCHOR_RAW = 430;
const int   CAL_ANCHOR_PCT = 44;

//  앵커에 맞춰 계산한 감마(430 → 44%)
// gamma = ln(44/100) / ln( base(430) ), base(430)= (1023-430)/1023 ≈ 0.5797
const float CAL_GAMMA = 1.506f;   // 소수점 3자리

// EMQX CA 인증서(PEM)
// 내용은 생략하겠습니다
static const char* ROOT_CA PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----

-----END CERTIFICATE-----
)EOF";
// =========================

WiFiClientSecure net;
PubSubClient mqtt(net);
unsigned long lastPub = 0;
const unsigned long PUB_INTERVAL_MS = 5 * 1000; // 슬립 안 쓸 때 주기 (임시 1분)

// SENSOR_PWR_PIN: -1 이면 전원 제어 없음, D5 등 유효 핀이면 제어함
const int SENSOR_PWR_PIN = -1;  // 전원 제어 안 쓰면 -1, 쓰면 D5 등으로 바꾸세요.

inline void sensorPower(bool on) {
  if (SENSOR_PWR_PIN < 0) return;      // 전원 제어 안 함
  pinMode(SENSOR_PWR_PIN, OUTPUT);
  digitalWrite(SENSOR_PWR_PIN, on ? HIGH : LOW);
}



int mapMoistureToPercent(int raw) {
  // 1) 기본 선형 매핑(끝값 고정: 0↔100)
  raw = constrain(raw, RAW_WET, RAW_DRY);
  int base = map(raw, RAW_WET, RAW_DRY, 100, 0);   // 0..100

  // 2) 감마 보정(중간만 휨, 0/100은 그대로)
  float bn = base / 100.0f;           // 0.0~1.0
  if (bn <= 0.0f) return 0;
  if (bn >= 1.0f) return 100;

  float adj = powf(bn, CAL_GAMMA);    // γ>1이면 중간값↓, γ<1이면 중간값↑
  int pct = (int)lroundf(adj * 100.0f);
  return constrain(pct, 0, 100);
}


int readMoisture() {
  sensorPower(true);            // 있으면 켬
  delay(300);                   // 센서 워밍업(환경에 맞게 100~500ms 조절)

  long sum = 0;
  const int N = 8;              // 노이즈 줄이기 위해 8회 평균
  for (int i = 0; i < N; ++i) {
    sum += analogRead(A0);
    delay(10);
  }

  sensorPower(false);           // 있으면 끔
  // 누설 줄이려면 핀을 High-Z로:
  if (SENSOR_PWR_PIN >= 0) pinMode(SENSOR_PWR_PIN, INPUT);

  return (int)(sum / N);
}




void syncClock() {
  // KST(UTC+9) 기준. 지역에 맞게 바꿔도 OK
  configTime(9 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Syncing time");
  time_t now = time(nullptr);
  while (now < 1700000000) { // 대략 2023-11-14 이후
    Serial.print(".");
    delay(500);
    now = time(nullptr);
  }
  Serial.println("\nTime synced.");
}

wl_status_t connectWiFi(const char* ssid, const char* pass, uint32_t timeout_ms=15000) {
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.disconnect(true); delay(200);

  Serial.printf("Connecting to %s ...\n", ssid);
  WiFi.begin(ssid, pass);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < timeout_ms) {
    delay(300); Serial.print(".");
  }
  Serial.println();
  Serial.printf("WiFi status=%d  RSSI=%d  IP=%s\n",
    WiFi.status(), WiFi.RSSI(), WiFi.localIP().toString().c_str());
  return (wl_status_t)WiFi.status();
}

void connectMQTT() {
  static BearSSL::X509List trust(ROOT_CA);
  net.setTrustAnchors(&trust);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setKeepAlive(60);
  mqtt.setBufferSize(1024);
  net.setTimeout(15000);
  while (!mqtt.connected()) {
    String cid = String("mcbaro-") + DEVICE_ID + "-" + String(ESP.getChipId(), HEX);
    Serial.print("MQTT connecting...");
    // LWT: 오프라인 표시(보관)
    if (mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASS,
                     TOPIC_STATUS, 1, true, "offline")) {
      Serial.println("connected");
      mqtt.publish(TOPIC_STATUS, "online", true);
    } else {
      Serial.print("failed, state="); Serial.println(mqtt.state());
      delay(3000);
    }
  }
}

void publishOnce() {
  int raw = readMoisture();
  int pct = mapMoistureToPercent(raw);

  // epoch time (NTP 동기화 덕분에 0이 아님)
  unsigned long ts = (unsigned long)time(nullptr);

  // 단순 JSON 문자열 구성(작게)
  char payload[160];
  snprintf(payload, sizeof(payload),
    "{\"ts\":%lu,\"deviceId\":\"%s\",\"moisture_raw\":%d,\"moisture_pct\":%d}",
    ts, DEVICE_ID, raw, pct);

  Serial.print("Publish: "); Serial.println(payload);
  mqtt.publish(TOPIC_TEL, payload, false); // QoS0. 신뢰 필요하면 PubSubClient의 QoS1 사용 라이브러리 고려
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("Hello from ESP8266");

  // ① 최초 Wi-Fi 연결
  if (connectWiFi(WIFI_SSID, WIFI_PASS) != WL_CONNECTED) {
  for (int i = 0; i < 10 && connectWiFi(WIFI_SSID, WIFI_PASS) != WL_CONNECTED; ++i) {
    delay(1000);
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skip MQTT.");
    return;
  }
}

  syncClock();      // TLS 검증을 위해 시간 동기화
  connectMQTT();

  if (SENSOR_PWR_PIN >= 0) {
    pinMode(SENSOR_PWR_PIN, OUTPUT);
    digitalWrite(SENSOR_PWR_PIN, LOW);   // 부팅 시 기본 OFF
  }


  // 한 번 발행 후 슬립 모드면 바로 슬립
  publishOnce();

  if (DEEP_SLEEP_MINUTES > 0) {
    Serial.println("DeepSleep...");
    mqtt.disconnect();
    WiFi.disconnect(true);
    delay(50);
    ESP.deepSleep((uint64_t)DEEP_SLEEP_MINUTES * 60ULL * 1000000ULL);
  }
}

void loop() {
  // 딥슬립 안 쓰는 경우에만 주기 발행
  if (DEEP_SLEEP_MINUTES == 0) {
    if (WiFi.status() != WL_CONNECTED) connectWiFi(WIFI_SSID, WIFI_PASS);
    if (!mqtt.connected()) connectMQTT();
    mqtt.loop();

    if (millis() - lastPub > PUB_INTERVAL_MS) {
      lastPub = millis();
      publishOnce();
    }
  }
}