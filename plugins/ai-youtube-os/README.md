# AI YouTube OS — Claude Code 플러그인

AI 에이전트(Claude Code)로 유튜브 채널을 **매일 빠지지 않고** 운영하는 구조를 플러그인으로 묶었습니다.
채널룸스튜디오가 유튜브 채널 6개를 운영하면서 쓰는 방식 그대로입니다.

> 솔직하게: 채널들은 2026년 9월 20일에 시작했고, 지금까지 가장 잘 된 쇼츠가 공개 후 약 3일간 1,229회입니다.
> 조회수 비법이 아니라 **매일 발행하는 구조**를 드리는 플러그인입니다.

## 설치

```
/plugin marketplace add channelroom-studio/ai-youtube-os
/plugin install ai-youtube-os@channelroom
```

## 명령

| 명령 | 하는 일 |
|---|---|
| `/ai-youtube-os:new-channel <폴더>` | 채널 폴더 생성: `channel.json`, `OPERATIONS.md`(작업 지시서), `state.json` |
| `/ai-youtube-os:daily <폴더>` | 오늘 회차를 7단계로 제작. 이미 만든 슬롯은 건너뜀 |
| `/ai-youtube-os:preflight <mp4> [srt]` | 업로드 전 기계 검사: 해상도, 길이, 오디오 유무·무음·클리핑, 자막 길이 |

스킬 `channel-operations`는 채널 폴더에서 작업할 때 자동으로 적용됩니다
(중복 생성 방지, 생성 job ID 즉시 기록, "업로드 시도 ≠ 완료").

## 매일 7단계

리서치 → 대본 → 음성 → 화면 → 렌더 → 자막·검수 → 업로드 예약

- 음성·영상 생성은 여러분이 연결한 도구(ElevenLabs, MiniMax, Higgsfield 등 MCP)를 씁니다.
  도구가 없으면 대본·장면 목록·생성 프롬프트까지 만들고 멈춥니다.
- 렌더: `scripts/render.py` — 장면 이미지 + 내레이션 → 세로 1080×1920 또는 가로 1920×1080 MP4 (FFmpeg 필요).
- 업로드는 `channel.json`에서 `daily_upload: true`로 직접 허락해야만 합니다. 결제·충전은 절대 자동으로 하지 않습니다.

## 이 플러그인이 실행하는 것

- **로컬 명령만 실행합니다**: `ffmpeg`, `ffprobe`, `python3`(동봉된 `scripts/render.py`, `scripts/preflight.py`), `mkdir`, `cp`, `ls`.
- **외부로 데이터를 보내지 않습니다.** 플러그인 자체에는 MCP 서버, 훅, 네트워크 요청이 없습니다.
- 리서치 단계의 웹 검색, 음성·영상 생성, 유튜브 업로드는 사용자가 따로 연결한 도구와 계정으로만, 사용자가 허락한 범위에서 이뤄집니다.
- 채널 폴더 안의 파일(`channel.json`, `state.json`, `runs/` 등)만 만들고 수정합니다.

## 요구 사항

- Claude Code, Python 3.9+, FFmpeg
- 음성·영상 생성 도구 계정 (선택)

## 더 필요하시면

- **가이드 전문**: [AI 에이전트로 유튜브 영상을 매일 자동으로 만드는 법](https://comfortable-radio-a87.notion.site/AI-3e9caee1d5478053bca1f576a6aa16f9)
- **노션 운영 OS 템플릿**: 채널·에피소드·지표·비용·권리를 한 곳에서 관리 ([무료 Lite](https://comfortable-radio-a87.notion.site/80dcaee1d547830495f7019b18851bc1))
- **1:1 세팅 서비스**: 이 구조를 여러분 PC와 채널에 맞게 원격으로 세팅해 드립니다 — 크몽 "채널룸스튜디오" (심사 중)
- 문의: hello@channelroom.app · 인스타그램 [@channelroom.studio](https://www.instagram.com/channelroom.studio/)

## 라이선스

MIT
