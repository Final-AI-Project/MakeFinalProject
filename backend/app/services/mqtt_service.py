# services/mqtt_service.py
from __future__ import annotations

import asyncio
import json
import re
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from core.config import settings         
from db.transaction import get_cursor   


class MQTTService:
    """
    - paho-mqtt(loop_start, 별도 스레드)에서 수신 → asyncio.Queue에 적재
    - FastAPI 이벤트 루프에서 컨슈머 태스크가 DB INSERT (db.transaction.get_cursor 사용)
    - payload 예:
      {"ts":1758176544,"deviceId":"1","moisture_raw":823,"moisture_pct":48}
    - humid_info 테이블 컬럼:
      idx(PK, AUTO_INCREMENT), plant_id(INT), humidity(FLOAT), humid_date(DATETIME)
    """

    def __init__(self) -> None:
        # --- MQTT 클라이언트 준비 ---
        self._client = mqtt.Client(client_id="plant-mqtt-sub", protocol=mqtt.MQTTv311)
        self._client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

        # TLS (CA 검증 권장)
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
        # payload 파싱
        try:
            payload_text = msg.payload.decode("utf-8")
            data = json.loads(payload_text)
        except Exception:
            data = {"raw": msg.payload.decode("utf-8", "ignore")}

        # 디버그/상태
        self.last = {"topic": msg.topic, **data}

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
        """
        humid_info INSERT
        - plant_id: deviceId
        - humidity: moisture_pct(없으면 humidity) 사용
        - humid_date: ts(UTC epoch) → UTC naive DATETIME
        """
        data: Dict[str, Any] = item["data"]

        # 1) humidity
        hv = data.get("moisture_pct", data.get("humidity"))
        if hv is None:
            return
        humidity = float(hv)

        # 2) plant_id: deviceId를 그대로 정수로 사용
        device_id_val = data.get("deviceId", None)
        plant_id: Optional[int] = None
        if isinstance(device_id_val, int):
            plant_id = device_id_val
        elif isinstance(device_id_val, str):
            s = device_id_val.strip()
            if s.isdigit():
                plant_id = int(s)

        if plant_id is None:
            # INT NOT NULL 제약: 숫자 아님 → 저장 스킵(원하면 기본값 0으로 변경 가능)
            print("[MQTT→DB] skip: deviceId is not numeric:", device_id_val)
            return

        # 3) humid_date
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        else:
            dt_utc = item["received_at"]  # 수신시각(UTC)
        dt_naive = dt_utc.replace(tzinfo=None)  # MySQL DATETIME은 naive

        sql = "INSERT INTO humid_info (plant_id, humidity, humid_date) VALUES (%s, %s, %s)"
        # 당신 프로젝트의 커서 컨텍스트(= 같은 DB 풀 재사용)
        async with get_cursor() as cursor:
            await cursor.execute(sql, (plant_id, humidity, dt_naive))


# 싱글톤 인스턴스
mqtt_service = MQTTService()
