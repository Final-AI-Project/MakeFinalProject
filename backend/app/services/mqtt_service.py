from __future__ import annotations

import asyncio
import json
import re
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from core.config import settings                  
from db.pool import get_db_connection 


class MQTTService:
    """
    - paho-mqtt(loop_start, 별도 스레드)에서 수신 → asyncio.Queue로 넘김
    - FastAPI 이벤트 루프에서 컨슈머가 core.database의 풀을 통해 INSERT 실행
    """
    def __init__(self) -> None:
        self._client = mqtt.Client(client_id="plant-mqtt-sub", protocol=mqtt.MQTTv311)
        self._client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

        ctx = ssl.create_default_context()
        ctx.load_verify_locations(settings.MQTT_CA_PATH)  
        self._client.tls_set_context(ctx)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._consumer_task: Optional[asyncio.Task] = None

        self.last: Optional[Dict[str, Any]] = None

    # -------- FastAPI lifespan에서 호출 --------
    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._consumer_task = loop.create_task(self._consumer())
        self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        self._client.loop_start()

    async def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

    # -------- MQTT 콜백 --------
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        topics = getattr(settings, "mqtt_topics_list", None) or [settings.MQTT_TOPICS]
        for t in topics:
            if t:
                client.subscribe(t, qos=1)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            data = {"raw": msg.payload.decode("utf-8", "ignore")}
        self.last = {"topic": msg.topic, **data}

        if self._loop:
            try:
                self._loop.call_soon_threadsafe(
                    self._queue.put_nowait,
                    {"topic": msg.topic, "data": data, "received_at": datetime.now(timezone.utc)},
                )
            except asyncio.QueueFull:
                # TODO: 로깅/메트릭
                pass

    # -------- 비동기 컨슈머(INSERT) --------
    async def _consumer(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                await self._save_row(item)
            except Exception as e:
                print("[MQTT→DB] error:", e)  # TODO: proper logging
            finally:
                self._queue.task_done()

    async def _save_row(self, item: Dict[str, Any]) -> None:
        """
        humid_info INSERT
        - plant_id: deviceId 문자열 끝자리 숫자(esp8266-soil-01 → 1)
        - humidity: moisture_pct (없으면 humidity)
        - humid_date: ts(UTC epoch) → UTC naive DATETIME
        """
        data: Dict[str, Any] = item["data"]

        # humidity
        hv = data.get("moisture_pct", data.get("humidity"))
        if hv is None:
            return
        humidity = float(hv)

        # plant_id
        device_id = str(data.get("deviceId", ""))
        m = re.search(r"(\d+)$", device_id)
        plant_id = int(m.group(1)) if m else 0

        # humid_date
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        else:
            dt_utc = item["received_at"]
        dt_naive = dt_utc.replace(tzinfo=None)

        sql = "INSERT INTO humid_info (plant_id, humidity, humid_date) VALUES (%s, %s, %s)"
        async with get_db_connection() as (conn, cursor):
            await cursor.execute(sql, (plant_id, humidity, dt_naive))
            # commit은 컨텍스트 매니저가 처리

mqtt_service = MQTTService()