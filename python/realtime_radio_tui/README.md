# Realtime Radio TUI

一个独立的 Python 子项目：从西班牙网络电台的 `m3u8` 流中提取音频，送入 Mistral `voxtral-mini-transcribe-realtime-2602`，并在 Textual TUI 中实时显示转写结果。

## 安装

```bash
cd python/realtime_radio_tui
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

设置 API Key：

```bash
export MISTRAL_API_KEY=your_key_here
```

## 运行

```bash
radio-transcribe-tui
```

也可以直接传入地址：

```bash
radio-transcribe-tui "https://example.com/live/index.m3u8"
```

## 说明

- 音频链路使用 `ffmpeg`，优先使用系统 `ffmpeg`，否则回退到 `imageio-ffmpeg` 自带二进制。
- 输出格式固定为 `pcm_s16le / 16kHz / mono`，与 Mistral Realtime 文档示例一致。
- 默认目标流式延迟是 `800ms`，可以在界面里调整。

