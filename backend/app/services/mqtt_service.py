# services/mqtt_service.py
from __future__ import annotations

import aiomysql
import asyncio
import json
import re
import ssl
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:
    KST = timezone(timedelta(hours=9))

from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from core.config import settings         
from db.transaction import get_cursor   

# 에러 코드 상수
ER_LOCK_WAIT_TIMEOUT = 1205
ER_LOCK_NOWAIT = 3572   # "NOWAIT"로 잠금 못 잡음
ER_DEADLOCK = 1213
ER_NO_REFERENCED_ROW = 1452  # FK 실패


class MQTTService:
    """
    - paho-mqtt(loop_start, 별도 스레드)에서 수신 → asyncio.Queue에 적재
    - FastAPI 이벤트 루프에서 컨슈머 태스크가 DB INSERT (db.transaction.get_cursor 사용)
    - payload 예:
      {"ts":1758176544,"deviceId":"1","moisture_raw":823,"moisture_pct":48}
    - humid_info 테이블 컬럼:
      idx(PK, AUTO_INCREMENT), device_id(INT), humidity(FLOAT), humid_date(DATETIME)
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
        data: Dict[str, Any] = item["data"]

        # humidity → INT(0~100)
        hv = data.get("moisture_pct", data.get("humidity"))
        if hv is None:
            return
        try:
            humidity = max(0, min(100, int(round(float(hv)))))
        except Exception:
            return

        # device_id → INT
        dv = data.get("deviceId")
        if isinstance(dv, int):
            device_id = dv
        elif isinstance(dv, str) and dv.strip().isdigit():
            device_id = int(dv.strip())
        else:
            print("[MQTT→DB] skip: deviceId not numeric:", dv)
            return

        # humid_date → DATE (KST 기준 날짜 권장)
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        else:
            dt_utc = item["received_at"]
        dt_date = dt_utc.astimezone(KST).date()

        # 재시도(지수 백오프)
        for attempt in range(4):  # 최대 4회 시도
            try:
                async with get_cursor() as cursor:
                    # 빠른 실패: 부모 행을 NOWAIT 공유잠금으로 확인 (잠겨있으면 바로 예외)
                    await cursor.execute(
                        "SELECT device_id FROM device_info WHERE device_id=%s FOR SHARE NOWAIT",
                        (device_id,)
                    )
                    # 부모가 잠겨있지 않으면 실제 INSERT
                    await cursor.execute(
                        "INSERT INTO humid_info (device_id, humidity, humid_date) VALUES (%s, %s, %s)",
                        (device_id, humidity, dt_date)
                    )
                return  # 성공
            except aiomysql.OperationalError as e:
                code = e.args[0] if e.args else None
                if code in (ER_LOCK_WAIT_TIMEOUT, ER_LOCK_NOWAIT, ER_DEADLOCK):
                    # 잠금 충돌 → 짧게 대기 후 재시도
                    backoff = 0.2 * (2 ** attempt)  # 0.2s, 0.4s, 0.8s, 1.6s
                    await asyncio.sleep(backoff)
                    continue
                raise
            except aiomysql.IntegrityError as e:
                # FK 실패: device_info에 없음 → 스킵
                if e.args and e.args[0] == ER_NO_REFERENCED_ROW:
                    print(f"[MQTT→DB] skip: unknown device_id={device_id}")
                    return
                raise

        print(f"[MQTT→DB] drop after retries: device_id={device_id}, humidity={humidity}, date={dt_date}")


# 싱글톤 인스턴스
mqtt_service = MQTTService()
