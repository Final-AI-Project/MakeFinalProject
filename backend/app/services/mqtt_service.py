from __future__ import annotations

import asyncio
import json
import ssl
from datetime import datetime, timezone, timedelta, date

from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from core.config import settings         
from db.transaction import get_cursor   

# UTC <> KST
KST = timezone(timedelta(hours=9))


class MQTTService:
    """
    - paho-mqtt(loop_start, 별도 스레드)에서 수신 → asyncio.Queue에 적재
    - FastAPI 이벤트 루프에서 컨슈머 태스크가 DB INSERT (db.transaction.get_cursor 사용)
    - payload 예:
      {"ts":1758176544,"deviceId":"1","moisture_raw":823,"moisture_pct":48}
    - humid_info 테이블 컬럼:
      device_id(INT), humidity(varchar(50)), sensor_digit(INT), humid_date(DATETIME)
    """

    def __init__(self) -> None:
        # --- MQTT 클라이언트 준비 ---
        self._client = mqtt.Client(client_id="plant-mqtt-sub", protocol=mqtt.MQTTv311)
        self._client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

        # TLS (CA 검증)
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(settings.MQTT_CA_PATH)
        self._client.tls_set_context(ctx)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # --- asyncio / 내부 상태 ---
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._consumer_task: Optional[asyncio.Task] = None

        # 디버그/상태 확인용
        self.last: Optional[Dict[str, Any]] = None

    # ---------- FastAPI lifespan에서 호출 ----------
    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """서비스 시작: 컨슈머 태스크 생성, MQTT 접속/수신루프 시작"""
        self._loop = loop
        self._consumer_task = loop.create_task(self._consumer())
        self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        self._client.loop_start()

    async def stop(self) -> None:
        """서비스 정리: MQTT/컨슈머 종료"""
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

    # ---------- MQTT 콜백 ----------
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        topics = getattr(settings, "mqtt_topics_list", None) or [settings.MQTT_TOPICS]
        for t in topics:
            if t:
                client.subscribe(t, qos=1)

    def _on_message(self, client, userdata, msg):
        parsed_ok = False
        payload_text = None
        try:
            payload_text = msg.payload.decode("utf-8")
            data = json.loads(payload_text)
            parsed_ok = True
        except Exception:
            payload_text = msg.payload.decode("utf-8", "ignore")
            data = {"raw": payload_text}

        self.last = {"topic": msg.topic, **data}

        # payload 콘솔 출력
        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        if parsed_ok:
            print(f"[{now}] [MQTT] topic={msg.topic} payload={payload_text}", flush=True)
        else:
            print(f"[{now}] [MQTT] topic={msg.topic} (non-JSON) payload={payload_text}", flush=True)

        if not self._loop:
            print("[MQTT] WARNING: _loop is None; did you call mqtt_service.start(loop)?", flush=True)
            return

        try:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait,
                {"topic": msg.topic, "data": data, "received_at": datetime.now(timezone.utc)},
            )
        except asyncio.QueueFull:
            print("[MQTT] ERROR: queue full; dropping message", flush=True)


        # 스레드 → asyncio 루프에 안전하게 enqueue
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(
                    self._queue.put_nowait,
                    {
                        "topic": msg.topic,
                        "data": data,
                        "received_at": datetime.now(timezone.utc),
                    },
                )
            except asyncio.QueueFull:
                # TODO: 로깅/메트릭
                pass

    # ---------- 비동기 컨슈머(INSERT) ----------
    async def _consumer(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                await self._save_row(item)
            except Exception as e:
                # TODO: proper logging
                print("[MQTT→DB] error:", e)
            finally:
                self._queue.task_done()

    async def _save_row(self, item: Dict[str, Any]) -> None:
        data: Dict[str, Any] = item["data"]

        # 1. device_id → INT
        dv = data.get("deviceId")
        if isinstance(dv, int):
            device_id = dv
        elif isinstance(dv, str) and dv.strip().isdigit():
            device_id = int(dv.strip())
        else:
            print("[MQTT→DB] skip: deviceId not numeric:", dv)
            return
        

        # 2. humidity → INT(0~100)
        hv = data.get("moisture_pct")
        if hv is None:
            return
        try:
            humidity = max(0, min(100, int(round(float(hv)))))
        except Exception:
            return
        
        # 3. sensor_digit → INT
        sv_raw = data.get("moisture_raw")
        sensor_digit: int | None
        if sv_raw is None:
            sensor_digit = None
        else:
            try:
                sensor_digit = int(float(sv_raw))  # 숫자/문자 모두 시도
            except (TypeError, ValueError):
                sensor_digit = None


        # 4. humid_date → DATETIME (KST 기준)
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        else:
            dt_utc = item["received_at"]
        dt_date = dt_utc.astimezone(KST)


        # INSERT
        async with get_cursor() as cursor:

            print(f"[MQTT→DB] insert try: device_id={device_id}, humidity={humidity}, " f"sensor_digit={sensor_digit}, humid_date={dt_date}", flush=True)

            await cursor.execute(
                """
                INSERT INTO humid_info (device_id, humidity, sensor_digit, humid_date)
                VALUES (%s, %s, %s, %s)
                """,
                (device_id, humidity, sensor_digit, dt_date)
            )
            conn = getattr(cursor, "connection", None) or getattr(cursor, "_connection", None)
            if conn is not None and hasattr(conn, "commit"):
                await conn.commit()
                print("[MQTT→DB] commit ok", flush=True)
            else:
                await cursor.execute("COMMIT")
                print("[MQTT→DB] commit via SQL ok", flush=True)


# 싱글톤 인스턴스
mqtt_service = MQTTService()
