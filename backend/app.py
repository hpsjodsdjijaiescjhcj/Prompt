"""
AI提示词管家 — Flask 后端 v2
"""

import logging
import time
from collections import deque

from flask import Flask, jsonify, request
from flask_cors import CORS

import llm_client
from classifier import classify_task
from prompt_generator import generate_prompt
from recommender import recommend_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 内存历史记录（简单实现，重启后丢失）
history: deque[dict] = deque(maxlen=50)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """分析用户需求，返回模型推荐和提示词"""
    data = request.get_json()
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "请输入您的需求"}), 400

    start_time = time.time()

    # 1. 智能任务分类
    classification = classify_task(user_input)

    # 2. 多维度模型推荐
    recommendations = recommend_models(classification)

    # 3. 为每个推荐模型生成专属提示词
    results = []
    for rec in recommendations:
        prompt = generate_prompt(user_input, rec, classification)
        results.append({
            "model": {
                "name": rec["name"],
                "provider": rec["provider"],
                "icon": rec["icon"],
                "color": rec["color"],
                "description": rec["description"],
                "strengths": rec["strengths"],
                "weaknesses": rec["weaknesses"],
                "best_for": rec["best_for"],
                "prompt_tips": rec["prompt_tips"],
                "match_pct": rec["match_pct"],
                "scores": rec["scores"],
                "cost": rec["cost"],
                "speed": rec["speed"],
                "context_window": rec["context_window"],
            },
            "reason": rec["reason"],
            "prompt": prompt,
        })

    elapsed = round(time.time() - start_time, 2)

    response_data = {
        "input": user_input,
        "classification": {
            "task_types": classification["task_types"],
            "complexity": classification.get("complexity", "medium"),
            "intent": classification.get("intent", user_input),
            "key_entities": classification.get("key_entities", []),
            "source": classification.get("source", "unknown"),
        },
        "recommendations": results,
        "meta": {
            "elapsed_seconds": elapsed,
            "llm_available": llm_client.is_available(),
        },
    }

    # 保存到历史
    history.appendleft({
        "id": int(time.time() * 1000),
        "input": user_input,
        "classification": response_data["classification"],
        "model_names": [r["model"]["name"] for r in results],
        "timestamp": time.time(),
    })

    return jsonify(response_data)


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取历史记录"""
    return jsonify({"history": list(history)})


@app.route("/api/health", methods=["GET"])
def health():
    """健康检查（含 Ollama 状态）"""
    ollama_ok = llm_client.check_ollama()
    return jsonify({
        "status": "ok",
        "ollama_available": ollama_ok,
        "ollama_model": llm_client.OLLAMA_MODEL if ollama_ok else None,
    })


if __name__ == "__main__":
    # 启动时检测 Ollama
    if llm_client.check_ollama():
        logger.info("Ollama 可用，将使用 LLM 进行智能分类和提示词生成")
    else:
        logger.warning("Ollama 不可用，将使用关键词匹配和模板生成（降级模式）")

    app.run(debug=True, port=5001)
