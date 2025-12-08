"""
麦克风录音模块 (服务器端)
依赖: sounddevice, numpy
提供函数: record_audio(duration, samplerate, channels) -> bytes(WAV)

说明: 为满足“所有依赖必须为 Python 库”的要求，本模块仅提供对本地音频设备的原始 WAV 录制
而不再包含 pydub/ffmpeg 编码或对外部二进制的依赖。录制结果始终为 WAV 字节数据。
"""

import io
import wave

try:
    import sounddevice as sd
    import numpy as np
except Exception:
    sd = None
    np = None


def record_audio(duration=5, samplerate=44100, channels=1):
    """录制音频并返回 WAV 格式的字节数据

    duration: 秒
    samplerate: 采样率
    channels: 通道数
    """
    if sd is None or np is None:
        raise RuntimeError('缺少依赖: 请安装 sounddevice 和 numpy')

    # 录音
    frames = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
    sd.wait()

    # 将 float32 转为 int16
    audio_int16 = (frames * 32767).astype(np.int16)

    # 写入WAV到内存
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(audio_int16.tobytes())

    return bio.getvalue()
