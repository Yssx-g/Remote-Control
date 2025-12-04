"""
屏幕流模块 - 使用 mss 捕获屏幕并提供 JPEG 字节帧
"""
import threading
import time
import queue
import io
import mss
from PIL import Image
import numpy as np

class ScreenStream:
    def __init__(self, region=None, fps=10, quality=70):
        """region: None 或 dict {left, top, width, height}
        fps: 采样帧率
        quality: JPEG质量
        """
        self.region = region
        self.fps = fps
        self.quality = quality
        self.is_streaming = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.thread = None

    def start(self):
        if self.is_streaming:
            return True, "屏幕流已在运行"
        self.is_streaming = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        time.sleep(0.05)
        return True, "屏幕流启动成功"

    def stop(self):
        self.is_streaming = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        # 清理队列
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Exception:
                break
        return True, "屏幕流已停止"

    def _capture_loop(self):
        frame_interval = 1.0 / max(1, self.fps)
        with mss.mss() as sct:
            monitor = sct.monitors[1] if self.region is None else self.region
            while self.is_streaming:
                start = time.time()
                try:
                    if self.region is None:
                        sct_img = sct.grab(monitor)
                    else:
                        sct_img = sct.grab({
                            'left': monitor['left'] + int(self.region.get('left', 0)),
                            'top': monitor['top'] + int(self.region.get('top', 0)),
                            'width': int(self.region.get('width', monitor['width'])),
                            'height': int(self.region.get('height', monitor['height']))
                        })

                    # 转为 PIL Image
                    img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)

                    # 压缩为 JPEG bytes
                    bio = io.BytesIO()
                    img.save(bio, format='JPEG', quality=self.quality, optimize=True)
                    jpeg_bytes = bio.getvalue()

                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except Exception:
                            pass
                    self.frame_queue.put(jpeg_bytes)

                except Exception as e:
                    # 捕获并继续
                    pass

                elapsed = time.time() - start
                to_sleep = frame_interval - elapsed
                if to_sleep > 0:
                    time.sleep(to_sleep)

    def get_frame(self, timeout=1.0):
        try:
            return True, self.frame_queue.get(timeout=timeout)
        except Exception:
            return False, "获取帧超时"
