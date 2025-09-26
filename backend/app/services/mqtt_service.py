from __future__ import annotations

import asyncio
import json
import ssl
from datetime import datetime, timezone, timedelta, date

from typing import Any, Dict, Optional, List

import paho.mqtt.client as mqtt

from core.config import settings         
from db.pool import get_pool
from db.transaction import get_cursor   

# UTC <> KST
KST = timezone(timedelta(hours=9))


class MQTTService:
    """
    - paho-mqtt(loop_start, 별도 스레드)에서 수신 → asyncio.Queue에 적재
    - FastAPI 이벤트 루프에서 컨슈머 태스크가 DB INSERT (db.transaction.get_cursor 사용)
    - payload 예:
      {"ts":1758176544,"deviceId":"1","moisture_raw":823,"moisture_pct":48}
    - humid 테이블 컬럼:
      device_id(INT), humidity(INT), sensor_digit(INT), humid_date(DATETIME)
    - 모든 식물에 공통으로 사용되는 습도 데이터 (device_id=1)
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

        # 배치 처리 제거 - 즉시 저장으로 변경

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
                print("[MQTT] ERROR: queue full; dropping message", flush=True)

    # ---------- 비동기 컨슈머(즉시 저장) ----------
    async def _consumer(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                # MQTT 데이터 수신 시 즉시 저장
                await self._save_row_immediate(item)
            except Exception as e:
                print("[MQTT→DB] error:", e)
            finally:
                self._queue.task_done()

    async def _save_row_immediate(self, item: Dict[str, Any]) -> None:
        """MQTT 데이터를 즉시 저장 (humid 테이블 사용)"""
        data = item["data"]
        
        # 데이터 파싱
        device_id = int(data.get("deviceId", 1))
        humidity = max(0, min(100, int(round(float(data.get("moisture_pct", 0))))))
        sensor_digit = int(float(data.get("moisture_raw", 0)))
        
        # datetime 변환
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        else:
            dt_utc = item["received_at"]
        dt_datetime = dt_utc.astimezone(KST)
        
        try:
            print(f"[MQTT→DB] immediate save: device_id={device_id}, humidity={humidity}, sensor_digit={sensor_digit}", flush=True)
            
            # 기존 백엔드의 연결 풀 사용 (간단하고 안정적)
            async with get_cursor() as cursor:
                # humid 테이블에 직접 INSERT (device_fk 불필요)
                await cursor.execute(
                    """
                    INSERT INTO humid (device_id, humidity, sensor_digit, humid_date)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (device_id, humidity, sensor_digit, dt_datetime)
                )
                
                print("[MQTT→DB] INSERT query executed successfully", flush=True)
                print("[MQTT→DB] immediate save ok", flush=True)
                
        except Exception as db_error:
            print(f"[MQTT→DB] database error: {db_error}", flush=True)
            # 락 타임아웃 오류는 재시도하지 않고 무시
            if "Lock wait timeout" in str(db_error):
                print(f"[MQTT→DB] SKIP: Lock timeout for device_id={device_id}, ignoring this message", flush=True)
                return
            # 기타 오류도 무시하고 계속 진행 (MQTT 데이터 손실 방지)
            print(f"[MQTT→DB] SKIP: Other error for device_id={device_id}, ignoring this message", flush=True)
            return




# 싱글톤 인스턴스
mqtt_service = MQTTService()
