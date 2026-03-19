#!/bin/bash
#
# 设计哲学提示词生成器
# 根据文章类型和主题生成增强的图片提示词
# 使用方法: bash design-philosophy.sh <文章类型> <主题>
#

# 文章类型对应的设计哲学
generate_philosophy() {
    local type="$1"
    local topic="$2"

    case "$type" in
        "干货教程"|"tutorial"|"教程")
            echo "Knowledge Clarity philosophy: Geometric precision, clear visual hierarchy, structured space, systematic organization. Clean grid-based composition with precise alignment. Color blocks create meaning zones. Typography minimal and refined - small sans-serif labels. Information encoded spatially through masterful visual orchestration. Meticulously crafted design."
            ;;
        "观点评论"|"opinion"|"评论")
            echo "Perspective Geometry philosophy: Angular tension, contrasting viewpoints, dynamic diagonal lines. Visual expression of multiple perspectives through layered geometric forms. Bold typography as architectural gesture. Spatial tension creates energy. Ideas expressed through visual weight and spatial opposition. Expert-level compositional balance."
            ;;
        "案例分析"|"case"|"案例")
            echo "Narrative Layers philosophy: Transparent color blocks, temporal flow, layered storytelling. Visual elements arranged to show depth and progression. Organic spatial relationships reveal narrative structure. Subtle typography floats within composition. Each layer carefully calibrated to guide the eye through the story. Painstaking attention to visual hierarchy."
            ;;
        "热点追踪"|"trending"|"热点")
            echo "Pulse Frequency philosophy: Repetitive wave patterns, gradient frequencies, dynamic energy flow. Visual rhythm suggests movement and urgency. Concentric circles and radiating lines create pulse-like effects. Color transitions mark intensity zones. Typography integrated as rhythmic accent. Masterfully orchestrated visual energy."
            ;;
        "科技前沿"|"tech"|"科技")
            echo "Future Logic philosophy: Clean lines, digital precision, futuristic aesthetic. Geometric forms suggest technological advancement. Cool color palette with electric accents. Grid-based layout with systematic precision. Typography sharp and technical. The composition feels like a diagram from tomorrow. Expertly crafted futuristic vision."
            ;;
        "情感故事"|"emotional"|"情感")
            echo "Emotional Resonance philosophy: Organic forms, flowing curves, warm color transitions. Visual elements arranged to evoke feeling and connection. Soft edges and gentle spatial relationships. Typography delicate and integrated. The composition breathes with emotional depth. Meticulously crafted to touch the heart."
            ;;
        "商务分析"|"business"|"商务")
            echo "Structured Authority philosophy: Bold geometric divisions, confident color blocks, strong visual hierarchy. Professional aesthetic with corporate precision. Clean lines and systematic organization. Typography authoritative and refined. The composition commands respect through expert visual balance. Master-level business design."
            ;;
        *)
            echo "Modern Minimalist philosophy: Clean composition, balanced spatial arrangement, refined color palette. Geometric precision meets artistic intuition. Negative space used deliberately. Typography minimal and purposeful. Every element placed with expert care. Meticulously crafted contemporary design."
            ;;
    esac
}

# 获取文章类型
ARTICLE_TYPE="$1"
TOPIC="$2"

if [ -z "$ARTICLE_TYPE" ]; then
    echo "使用方法: bash design-philosophy.sh \"文章类型\" \"主题\""
    echo ""
    echo "文章类型选项:"
    echo "  干货教程, tutorial, 教程"
    echo "  观点评论, opinion, 评论"
    echo "  案例分析, case, 案例"
    echo "  热点追踪, trending, 热点"
    echo "  科技前沿, tech, 科技"
    echo "  情感故事, emotional, 情感"
    echo "  商务分析, business, 商务"
    exit 1
fi

# 生成设计哲学
PHILOSOPHY=$(generate_philosophy "$ARTICLE_TYPE" "$TOPIC")

# 输出增强的提示词
if [ -n "$TOPIC" ]; then
    echo "$PHILOSOPHY Theme: $TOPIC. Professional poster design, 900x500 pixels, museum-quality composition, expert craftsmanship, refined color palette."
else
    echo "$PHILOSOPHY Professional poster design, 900x500 pixels, museum-quality composition."
fi
