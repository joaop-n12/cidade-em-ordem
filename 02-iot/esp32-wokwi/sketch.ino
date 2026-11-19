// Cidade em Ordem - GS 2026.2
// ESP32 no caminhao de coleta: MPU6050 + HC-SR04, envia os dados por MQTT

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";
const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT = 1883;
const char* ID_VEICULO = "caminhao-01";

const char* TOPICO_TELEMETRIA = "cidadeemordem/caminhao-01/telemetria";
const char* TOPICO_EVENTO     = "cidadeemordem/caminhao-01/evento";
const char* TOPICO_COMANDO    = "cidadeemordem/caminhao-01/comando";
const char* TOPICO_STATUS     = "cidadeemordem/caminhao-01/status";

const int PINO_TRIG = 13;
const int PINO_ECHO = 14;
const int PINO_LED_ALERTA = 21;
const int PINO_LED_CONECTADO = 16;
const int PINO_SDA = 22;  // I2C do MPU6050
const int PINO_SCL = 23;

// limiares
const float LIMIAR_IMPACTO_G = 1.5;
const float LIMIAR_PROFUNDIDADE_CM = 4.0;
const unsigned long INTERVALO_TELEMETRIA_MS = 3000;
const unsigned long INTERVALO_MIN_EVENTO_MS = 4000; // nao repetir o mesmo buraco

// rota simulada (o Wokwi nao tem GPS)
const double ROTA[][2] = {
  {-23.53980, -46.57710}, {-23.54020, -46.57630}, {-23.54080, -46.57520},
  {-23.54150, -46.57400}, {-23.54230, -46.57280}, {-23.54310, -46.57120},
};
const int TAMANHO_ROTA = sizeof(ROTA) / sizeof(ROTA[0]);

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
Adafruit_MPU6050 mpu;
bool mpuOk = false;

float distanciaBaseCm = 40.0;  // calibrada no setup
unsigned long ultimoEnvio = 0;
unsigned long ultimoEvento = 0;
unsigned long sequencia = 0;
int pontoRota = 0;

float lerDistanciaCm() {
  digitalWrite(PINO_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PINO_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PINO_TRIG, LOW);
  long duracao = pulseIn(PINO_ECHO, HIGH, 30000);  // timeout 30 ms
  if (duracao == 0) return -1;
  return duracao * 0.0343 / 2.0;
}

float lerAceleracaoG() {
  if (!mpuOk) return 1.0;
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float mod = sqrt(a.acceleration.x * a.acceleration.x +
                   a.acceleration.y * a.acceleration.y +
                   a.acceleration.z * a.acceleration.z);
  return mod / 9.80665;
}

void calibrar() {
  float soma = 0;
  int validas = 0;
  for (int i = 0; i < 10; i++) {
    float d = lerDistanciaCm();
    if (d > 0) { soma += d; validas++; }
    delay(50);
  }
  if (validas > 0) distanciaBaseCm = soma / validas;
  Serial.printf("[CALIBRACAO] distancia base ao asfalto = %.1f cm\n", distanciaBaseCm);
}

void conectarWiFi() {
  Serial.print("[WIFI] conectando");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(250);
    Serial.print(".");
    tentativas++;
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " ok" : " falhou (tentara de novo)");
}

void aoReceberComando(char* topico, byte* payload, unsigned int tamanho) {
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload, tamanho)) {
    Serial.println("[MQTT] comando invalido ignorado");
    return;
  }
  const char* acao = doc["acao"] | "";
  Serial.printf("[MQTT] comando recebido: %s\n", acao);
  if (strcmp(acao, "alerta_critico") == 0) {
    for (int i = 0; i < 6; i++) {
      digitalWrite(PINO_LED_ALERTA, i % 2 == 0);
      delay(150);
    }
    digitalWrite(PINO_LED_ALERTA, HIGH);
  } else if (strcmp(acao, "limpar") == 0) {
    digitalWrite(PINO_LED_ALERTA, LOW);
  }
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    if (WiFi.status() != WL_CONNECTED) conectarWiFi();
    String clientId = String("cidadeemordem-") + ID_VEICULO + "-" + String(random(0xffff), HEX);
    Serial.print("[MQTT] conectando ao broker... ");
    // last will -> offline
    if (mqtt.connect(clientId.c_str(), TOPICO_STATUS, 1, true, "{\"status\":\"offline\"}")) {
      Serial.println("ok");
      mqtt.publish(TOPICO_STATUS, "{\"status\":\"online\"}", true);
      mqtt.subscribe(TOPICO_COMANDO, 1);
      digitalWrite(PINO_LED_CONECTADO, HIGH);
    } else {
      Serial.printf("falhou (rc=%d), nova tentativa em 2 s\n", mqtt.state());
      digitalWrite(PINO_LED_CONECTADO, LOW);
      delay(2000);
    }
  }
}

void publicar(const char* topico, float g, float distancia, float profundidade, const char* tipo, const char* severidade) {
  StaticJsonDocument<384> doc;
  doc["veiculo"] = ID_VEICULO;
  doc["seq"] = sequencia++;
  doc["tipo"] = tipo;
  doc["lat"] = ROTA[pontoRota][0];
  doc["lon"] = ROTA[pontoRota][1];
  doc["impacto_g"] = round(g * 100) / 100.0;
  doc["distancia_cm"] = round(distancia * 10) / 10.0;
  doc["profundidade_cm"] = round(profundidade * 10) / 10.0;
  if (severidade) doc["severidade"] = severidade;
  doc["uptime_ms"] = millis();

  char buffer[384];
  size_t n = serializeJson(doc, buffer);
  bool ok = mqtt.publish(topico, buffer, n);
  Serial.printf("[PUB %s] %s %s\n", ok ? "ok" : "FALHA", topico, buffer);
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_TRIG, OUTPUT);
  pinMode(PINO_ECHO, INPUT);
  pinMode(PINO_LED_ALERTA, OUTPUT);
  pinMode(PINO_LED_CONECTADO, OUTPUT);

  Wire.begin(PINO_SDA, PINO_SCL);
  mpuOk = mpu.begin();
  if (mpuOk) {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    Serial.println("[MPU6050] ok");
  } else {
    Serial.println("[MPU6050] nao encontrado - seguindo so com o ultrassonico");
  }

  calibrar();
  conectarWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(aoReceberComando);
  mqtt.setBufferSize(512);
}

void loop() {
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();

  float g = lerAceleracaoG();
  float distancia = lerDistanciaCm();
  if (distancia < 0) {
    Serial.println("[HC-SR04] leitura invalida descartada");
    delay(200);
    return;
  }
  float profundidade = max(0.0f, distancia - distanciaBaseCm);
  float variacaoG = fabs(g - 1.0);

  bool impacto = variacaoG >= LIMIAR_IMPACTO_G;
  bool depressao = profundidade >= LIMIAR_PROFUNDIDADE_CM;
  unsigned long agora = millis();

  if ((impacto || depressao) && agora - ultimoEvento > INTERVALO_MIN_EVENTO_MS) {
    const char* severidade = (variacaoG >= 2.0 || profundidade >= 8.0) ? "alta" : "moderada";
    publicar(TOPICO_EVENTO, g, distancia, profundidade, "possivel_buraco", severidade);
    ultimoEvento = agora;
  }

  if (agora - ultimoEnvio > INTERVALO_TELEMETRIA_MS) {
    publicar(TOPICO_TELEMETRIA, g, distancia, profundidade, "telemetria", nullptr);
    ultimoEnvio = agora;
    pontoRota = (pontoRota + 1) % TAMANHO_ROTA;
  }

  delay(100);
}
