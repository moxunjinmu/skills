# -*- coding: utf-8 -*-
"""
微信公众号艺术配图生成器示例脚本
基于设计哲学创作艺术级封面图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import numpy as np
import os
from datetime import datetime


def create_knowledge_clarity_artwork(topic, output_path):
    """
    创建 Knowledge Clarity（知识清晰）风格的艺术作品
    适合：干货教程类文章

    设计哲学：几何精度、清晰层次、系统化组织
    """
    fig, ax = plt.subplots(1, 1, figsize=(9, 5), dpi=100)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # 背景色 - 清新的浅灰蓝
    ax.add_patch(Rectangle((0, 0), 9, 5, facecolor='#f0f4f8', edgecolor='none'))

    # 主要几何形状 - 精确的网格系统
    colors = ['#2d3748', '#4299e1', '#48bb78', '#ed8936']

    # 大色块 - 清晰的层次结构
    ax.add_patch(Rectangle((0.5, 1), 2.5, 3, facecolor=colors[0], alpha=0.9))
    ax.add_patch(Rectangle((3.5, 0.5), 2, 2, facecolor=colors[1], alpha=0.8))
    ax.add_patch(Rectangle>(3.5, 3), 2, 1.5, facecolor=colors[2], alpha=0.7))
    ax.add_patch(Rectangle((6.2, 1), 2.3, 3, facecolor=colors[3], alpha=0.85))

    # 装饰线条 - 网格精度
    for x in [0.5, 3.5, 6.2, 8.5]:
        ax.plot([x, x], [0.3, 4.7], color='#cbd5e0', linewidth=0.5, alpha=0.5)

    # 小色块点缀
    for i in range(5):
        ax.add_patch(Circle((1.25 + i*0.3, 4.3), 0.08, facecolor='#ffffff', alpha=0.6))

    # 主题文字（极简）
    ax.text(4.5, 0.25, topic.upper(), ha='center', va='bottom',
            fontsize=8, color='#4a5568', fontweight='light',
            fontfamily='sans-serif', letter_spacing=2)

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0.1,
                facecolor='#f0f4f8', edgecolor='none')
    plt.close()

    print(f"✓ Knowledge Clarity 风格作品已保存: {output_path}")


def create_perspective_geometry_artwork(topic, output_path):
    """
    创建 Perspective Geometry（视角几何）风格的艺术作品
    适合：观点评论类文章

    设计哲学：角度张力、动态对比、视觉冲突
    """
    fig, ax = plt.subplots(1, 1, figsize=(9, 5), dpi=100)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # 背景 - 戏剧性的深色
    ax.add_patch(Rectangle((0, 0), 9, 5, facecolor='#1a202c', edgecolor='none'))

    # 斜切的几何形状 - 动态角度
    colors = ['#f6ad55', '#fc8181', '#63b3ed', '#68d391']

    # 主形状 - 带角度的矩形
    vertices1 = [(1, 1), (4, 0.5), (4.5, 3.5), (1.5, 4)]
    ax.add_patch(patches.Polygon(vertices1, facecolor=colors[0], alpha=0.9))

    vertices2 = [(4.5, 0.3), (7.5, 1), (7, 4), (5, 3.8)]
    ax.add_patch(patches.Polygon(vertices2, facecolor=colors[1], alpha=0.85))

    vertices3 = [(7.8, 0.5), (8.8, 1.5), (8.5, 4.5), (7.5, 3.5)]
    ax.add_patch(patches.Polygon(vertices3, facecolor=colors[2], alpha=0.8))

    # 叠加的小形状 - 创造层次
    ax.add_patch(Circle((2.5, 2.5), 0.3, facecolor='#ffffff', alpha=0.3))
    ax.add_patch(Circle((6, 2.5), 0.25, facecolor='#ffffff', alpha=0.25))

    # 动态线条
    ax.plot([0.5, 8.5], [4.8, 0.2], color='#ffffff', linewidth=0.5, alpha=0.3)
    ax.plot([0.5, 8.5], [0.2, 4.8], color='#ffffff', linewidth=0.5, alpha=0.3)

    # 主题文字
    ax.text(4.5, 0.15, topic.upper(), ha='center', va='bottom',
            fontsize=8, color='#e2e8f0', fontweight='medium',
            fontfamily='sans-serif')

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0.1,
                facecolor='#1a202c', edgecolor='none')
    plt.close()

    print(f"✓ Perspective Geometry 风格作品已保存: {output_path}")


def create_narrative_layers_artwork(topic, output_path):
    """
    创建 Narrative Layers（叙事层叠）风格的艺术作品
    适合：案例分析类文章

    设计哲学：层叠透明、时间流动、故事深度
    """
    fig, ax = plt.subplots(1, 1, figsize=(9, 5), dpi=100)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # 背景 - 温暖的米色
    ax.add_patch(Rectangle((0, 0), 9, 5, facecolor='#faf5f0', edgecolor='none'))

    # 层叠的透明形状 - 叙事层次
    colors = ['#9f7aea', '#ed8936', '#4299e1', '#48bb78', '#f6ad55']

    # 大的透明色块
    for i, color in enumerate(colors):
        alpha = 0.15 + i * 0.05
        offset = i * 0.3
        ax.add_patch(FancyBboxPatch((0.8 + offset, 1 + offset*0.5),
                                    7.4 - offset*2, 3 - offset,
                                    boxstyle="round,pad=0.1",
                                    facecolor=color, alpha=alpha,
                                    edgecolor='none'))

    # 时间流动的元素
    for i in range(8):
        x = 1.5 + i * 0.9
        size = 0.15 + i * 0.03
        ax.add_patch(Circle((x, 3.5), size, facecolor=colors[i % len(colors)],
                           alpha=0.6))

    # 连线 - 故事的延续
    for i in range(7):
        x1 = 1.5 + i * 0.9
        x2 = 1.5 + (i + 1) * 0.9
        ax.plot([x1, x2], [3.5, 3.5], color='#cbd5e0',
                linewidth=1, alpha=0.5)

    # 主题文字
    ax.text(4.5, 0.25, topic.upper(), ha='center', va='bottom',
            fontsize=8, color='#4a5568', fontweight='light',
            fontfamily='sans-serif')

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0.1,
                facecolor='#faf5f0', edgecolor='none')
    plt.close()

    print(f"✓ Narrative Layers 风格作品已保存: {output_path}")


def generate_artwork(topic, article_type, output_dir=None):
    """
    根据文章类型生成艺术作品

    :param topic: 文章主题
    :param article_type: 文章类型
    :param output_dir: 输出目录（默认为当前目录）
    """
    if output_dir is None:
        output_dir = os.getcwd()

    # 生成文件名
    date_str = datetime.now().strftime("%Y%m%d")
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_topic}-{date_str}-art.png"
    output_path = os.path.join(output_dir, filename)

    # 根据文章类型选择风格
    if article_type in ["干货教程", "tutorial", "教程"]:
        create_knowledge_clarity_artwork(topic, output_path)
    elif article_type in ["观点评论", "opinion", "评论"]:
        create_perspective_geometry_artwork(topic, output_path)
    elif article_type in ["案例分析", "case", "案例"]:
        create_narrative_layers_artwork(topic, output_path)
    else:
        # 默认使用 Knowledge Clarity
        create_knowledge_clarity_artwork(topic, output_path)

    return output_path


if __name__ == "__main__":
    # 示例使用
    print("微信公众号艺术配图生成器\n")

    # 示例1：干货教程类
    print("示例1：生成干货教程类封面")
    generate_artwork("AI教育", "干货教程")

    # 示例2：观点评论类
    print("\n示例2：生成观点评论类封面")
    generate_artwork("经济政策分析", "观点评论")

    # 示例3：案例分析类
    print("\n示例3：生成案例分析类封面")
    generate_artwork("成功案例研究", "案例分析")

    print("\n✅ 所有示例生成完成！")
