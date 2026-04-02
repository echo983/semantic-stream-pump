# Realtime Radio TUI

`realtime_radio_tui` 是一个独立的 Python 子项目，用于把网络电视/电台 `m3u8` 音频流接入 Mistral，实时显示：

- 左侧：原始转写
- 右侧：整理后的目标语言翻译

当前默认链路：

- 音频转写：`voxtral-mini-transcribe-realtime-2602`
- 翻译与整理：`mistral-small-2603`
- 界面：Textual TUI

## 功能概览

- 从 `m3u8` / HLS 流中提取音频
- 使用 `ffmpeg` 转成 `pcm_s16le / 16kHz / mono`
- 通过 Mistral Realtime 做流式转写
- 将转写结果按批次送入翻译模型
- 使用最近几段原文与译文作为上下文，提升连续性
- 在 TUI 中双栏显示原文与译文

## 安装

```bash
cd python/realtime_radio_tui
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

API Key 读取顺序：

1. 环境变量 `MISTRAL_API_KEY`
2. 仓库根目录 `.env`

根目录 `.env` 示例：

```env
MISTRAL_API_KEY=your_real_key_here
```

## 启动

推荐从仓库根目录直接启动当前源码版本：

```bash
cd /home/edwin/myProjects/semantic-stream-pump
./python/realtime_radio_tui/run_local.sh
```

指定流地址：

```bash
./python/realtime_radio_tui/run_local.sh "https://rtvelivestream.rtve.es/rtvesec/la2/la2_main_dvr.m3u8"
```

不建议优先使用旧的 `radio-transcribe-tui` console script，因为本地 editable 安装版本可能落后于当前源码。

## 界面说明

- `M3U8 stream URL`：输入直播流地址
- `Target delay (ms)`：传给 Mistral Realtime 的目标流式延迟，不是 `ffmpeg` 参数
- `Translate to`：目标翻译语言，例如 `Chinese`、`English`、`Japanese`
- `Translation model`：当前默认 `mistral-small-2603`

`Start` 开始处理，`Stop` 停止当前会话，`Clear` 清空左右面板。

## 模型与策略

转写层强调实时性，翻译层强调可读性与连续性。

- 原文转写直接显示 Mistral Realtime 增量结果
- 翻译层不会对每个 token 单独调用模型
- 只有在文本达到较完整的句子/片段后，才批量翻译
- 翻译 prompt 会带最近几段原文和译文作为短上下文

这样做的目标是提高：

- 断句质量
- 标点与换行
- 术语一致性
- 跨句连贯性

## 已知限制

- HLS 源天然是分片流，实时性受上游分片长度影响很大
- `*_dvr.m3u8` 这类源通常延迟更高
- 不同源站可能要求特定请求头或有访问限制
- 当前实现更适合广播/电视流，不是为 WebRTC 通话链路设计

## 验证

运行测试：

```bash
cd /home/edwin/myProjects/semantic-stream-pump
PYTHONPATH=python/realtime_radio_tui/src python/realtime_radio_tui/.venv/bin/python -m unittest discover -s python/realtime_radio_tui/tests -v
```

语法检查：

```bash
python3 -m compileall python/realtime_radio_tui/src
```
