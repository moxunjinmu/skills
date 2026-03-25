#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱 AI 语音识别 (ASR) 功能
支持 GLM-ASR-2512 模型进行语音转文字
"""

import os
import sys
import base64
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any


class ZhipuASR:
    """智谱 AI 语音识别客户端"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 ASR 客户端

        Args:
            api_key: 智谱 API 密钥，如果不提供则从环境变量 ZHIPU_API_KEY 读取
        """
        self.api_key = api_key or os.environ.get('ZHIPU_API_KEY')
        if not self.api_key:
            raise ValueError("API Key 未提供，请设置 ZHIPU_API_KEY 环境变量或传入 api_key 参数")

        self.api_url = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
        self.model = "glm-asr-2512"

    def transcribe_file(
        self,
        audio_file: str,
        hotwords: Optional[List[str]] = None,
        prompt: Optional[str] = None,
        stream: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用音频文件进行语音识别

        Args:
            audio_file: 音频文件路径（支持 .wav 和 .mp3 格式）
            hotwords: 热词表，用于提升特定领域词汇识别率（建议不超过100个）
            prompt: 在长文本场景中，可以提供之前的转录结果作为上下文（建议小于8000字）
            stream: 是否使用流式输出
            user_id: 终端用户的唯一ID

        Returns:
            包含识别结果的字典

        Raises:
            FileNotFoundError: 音频文件不存在
            ValueError: 音频格式不支持或参数错误
            requests.RequestException: API 请求失败
        """
        # 检查文件是否存在
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")

        # 检查文件扩展名
        if audio_path.suffix.lower() not in ['.wav', '.mp3']:
            raise ValueError(f"不支持的音频格式: {audio_path.suffix}，仅支持 .wav 和 .mp3 格式")

        # 检查文件大小（限制 25MB）
        file_size = audio_path.stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            raise ValueError(f"音频文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持 25MB")

        # 准备请求数据
        data = {
            'model': self.model,
            'stream': 'true' if stream else 'false'
        }

        # 添加可选参数
        files = {
            'file': (audio_path.name, open(audio_path, 'rb'), audio_path.suffix)
        }

        if prompt:
            data['prompt'] = prompt

        if hotwords:
            if len(hotwords) > 100:
                raise ValueError(f"热词表数量过多: {len(hotwords)}，最大支持 100 个")
            # 将热词列表转换为 JSON 数组格式
            data['hotwords'] = ','.join(hotwords)

        if user_id:
            if len(user_id) < 6 or len(user_id) > 128:
                raise ValueError("user_id 长度要求：至少6个字符，最多128个字符")
            data['user_id'] = user_id

        # 发送请求
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            print(f"正在识别音频文件: {audio_file} ({file_size / 1024:.2f}KB)")
            response = requests.post(
                self.api_url,
                headers=headers,
                data=data,
                files=files
            )
            response.raise_for_status()

            result = response.json()
            print("识别成功！")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"API 请求失败: {e}"
            try:
                error_detail = response.json()
                if 'error' in error_detail:
                    error_msg += f" - {error_detail['error']}"
            except:
                pass
            raise requests.RequestException(error_msg)
        finally:
            # 关闭文件句柄
            if 'file' in files:
                files['file'][1].close()

    def transcribe_base64(
        self,
        audio_base64: str,
        filename: str = "audio.wav",
        hotwords: Optional[List[str]] = None,
        prompt: Optional[str] = None,
        stream: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 Base64 编码的音频数据进行语音识别

        Args:
            audio_base64: 音频文件的 Base64 编码字符串
            filename: 音频文件名（用于确定格式，如 audio.wav 或 audio.mp3）
            hotwords: 热词表，用于提升特定领域词汇识别率
            prompt: 在长文本场景中，可以提供之前的转录结果作为上下文
            stream: 是否使用流式输出
            user_id: 终端用户的唯一ID

        Returns:
            包含识别结果的字典
        """
        # 准备请求数据
        data = {
            'model': self.model,
            'file_base64': audio_base64,
            'stream': 'true' if stream else 'false'
        }

        if prompt:
            data['prompt'] = prompt

        if hotwords:
            if len(hotwords) > 100:
                raise ValueError(f"热词表数量过多: {len(hotwords)}，最大支持 100 个")
            data['hotwords'] = ','.join(hotwords)

        if user_id:
            if len(user_id) < 6 or len(user_id) > 128:
                raise ValueError("user_id 长度要求：至少6个字符，最多128个字符")
            data['user_id'] = user_id

        # 发送请求
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'multipart/form-data'
        }

        try:
            print(f"正在识别 Base64 编码的音频: {filename}")
            response = requests.post(
                self.api_url,
                headers=headers,
                data=data
            )
            response.raise_for_status()

            result = response.json()
            print("识别成功！")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"API 请求失败: {e}"
            try:
                error_detail = response.json()
                if 'error' in error_detail:
                    error_msg += f" - {error_detail['error']}"
            except:
                pass
            raise requests.RequestException(error_msg)


def format_result(result: Dict[str, Any]) -> str:
    """格式化识别结果"""
    output = []
    output.append("=" * 60)
    output.append("语音识别结果")
    output.append("=" * 60)
    output.append(f"任务 ID: {result.get('id', 'N/A')}")
    output.append(f"模型: {result.get('model', 'N/A')}")
    output.append(f"请求 ID: {result.get('request_id', 'N/A')}")

    created = result.get('created')
    if created:
        import datetime
        created_time = datetime.datetime.fromtimestamp(created)
        output.append(f"创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")

    output.append("-" * 60)
    output.append("识别文本:")
    output.append(result.get('text', ''))
    output.append("=" * 60)

    return "\n".join(output)


def main():
    """命令行主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='智谱 AI 语音识别工具 - 使用 GLM-ASR-2512 模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python zhipu_asr.py audio.wav

  # 使用热词提升特定领域识别
  python zhipu_asr.py audio.wav --hotwords "智谱,AI,语音识别"

  # 指定 API Key
  python zhipu_asr.py audio.wav --api-key YOUR_API_KEY

  # 设置环境变量后使用
  export ZHIPU_API_KEY=YOUR_API_KEY
  python zhipu_asr.py audio.wav
        """
    )

    parser.add_argument(
        'audio_file',
        help='音频文件路径（支持 .wav 和 .mp3 格式）'
    )

    parser.add_argument(
        '--api-key',
        help='智谱 API 密钥（如果未设置，则从环境变量 ZHIPU_API_KEY 读取）'
    )

    parser.add_argument(
        '--hotwords',
        nargs='+',
        help='热词表，用空格分隔（最多 100 个词）'
    )

    parser.add_argument(
        '--prompt',
        help='上下文提示词（之前的转录结果，建议小于 8000 字）'
    )

    parser.add_argument(
        '--user-id',
        help='终端用户唯一 ID（6-128 字符）'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='将识别结果保存到指定文件'
    )

    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='仅输出识别文本，不显示其他信息'
    )

    args = parser.parse_args()

    try:
        # 初始化客户端
        asr = ZhipuASR(api_key=args.api_key)

        # 执行语音识别
        result = asr.transcribe_file(
            audio_file=args.audio_file,
            hotwords=args.hotwords,
            prompt=args.prompt,
            stream=False,
            user_id=args.user_id
        )

        # 输出结果
        text = result.get('text', '')

        if args.quiet:
            # 仅输出文本
            print(text)
        else:
            # 格式化输出
            print(format_result(result))

        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"\n识别结果已保存到: {args.output}")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
