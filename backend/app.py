"""
AI提示词管家 — Flask 后端 v2
"""

import logging
import re
import time
import uuid

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from dotenv import load_dotenv
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# 加载 backend/.env 中的环境变量（如 GEMINI_API_KEY）
load_dotenv()

import llm_client
from api.openapi import OPENAPI_SPEC
from api.schemas import SCHEMAS
from classifier import classify_task
from infrastructure.logging_config import configure_logging
from orchestrator import (
    ClarifyValidationError,
    confirm_spec,
    execute_session,
    start_workflow,
    submit_clarifications,
    validate_session_output,
)
try:
    from orchestrator.async_jobs import enqueue_execute, enqueue_validate, get_job
    ASYNC_JOB_AVAILABLE = True
except Exception:
    ASYNC_JOB_AVAILABLE = False

    def enqueue_execute(*args, **kwargs):
        raise RuntimeError("Async job queue is unavailable. Install celery and configure Redis.")

    def enqueue_validate(*args, **kwargs):
        raise RuntimeError("Async job queue is unavailable. Install celery and configure Redis.")

    def get_job(*args, **kwargs):
        raise RuntimeError("Async job queue is unavailable. Install celery and configure Redis.")
from infrastructure import acquire_lock, cache_response, read_cached_response, release_lock
from infrastructure.errors import ERROR_CODES, error_response
from infrastructure.history_store import build_history_store
from infrastructure.redis_client import redis_available
from infrastructure.db import mysql_available, init_mysql_schema
from middleware.auth import enforce_api_key_auth
from middleware.rate_limit import enforce_rate_limit
from middleware.validation import validate_json_payload
from prompt_generator import generate_prompt
from recommender import recommend_models
from api.routes_v2 import orchestration_bp, init_orchestration_service
from orchestrator.service_v2 import OrchestrationService

configure_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

history_store = build_history_store()
REQUEST_COUNT = Counter("taskforge_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("taskforge_http_request_latency_seconds", "HTTP latency", ["method", "path"])


@app.before_request
def _request_context():
    g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    g.started_at = time.time()
    auth_err = enforce_api_key_auth()
    if auth_err:
        return auth_err
    rate_err = enforce_rate_limit()
    if rate_err:
        return rate_err


@app.after_request
def _request_log(resp):
    elapsed_sec = time.time() - getattr(g, "started_at", time.time())
    elapsed_ms = int(elapsed_sec * 1000)
    REQUEST_COUNT.labels(request.method, request.path, str(resp.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.path).observe(elapsed_sec)
    logger.info(
        "request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
        getattr(g, "request_id", ""),
        request.method,
        request.path,
        resp.status_code,
        elapsed_ms,
    )
    resp.headers["X-Request-Id"] = getattr(g, "request_id", "")
    return resp


def _append_history(
    *,
    input_text: str,
    task_type: str,
    source: str,
    model_names: list[str] | None = None,
):
    task_type_map = {
        "email": "writing",
        "writing": "writing",
        "code": "coding",
        "generic": "reasoning",
        "other": "reasoning",
    }
    mapped = task_type_map.get(task_type, task_type or "reasoning")
    history_store.append(
        {
            "id": str(uuid.uuid4()),
            "input": input_text,
            "classification": {
                "task_types": [{"type": mapped, "confidence": 0.9}],
                "complexity": "medium",
                "intent": input_text,
                "source": source,
            },
            "model_names": model_names or [],
            "timestamp": time.time(),
        }
    )

# 模型名称常见写法（含版本/后缀），用于识别“只输入模型名”的场景
MODEL_NAME_RE = re.compile(
    r"^(?:"
    r"(?:chatgpt|gpt(?:[-_. ]?\d+(?:\.\d+)*)?)"
    r"|(?:claude(?:[-_. ]?(?:\d+(?:\.\d+)*|sonnet|opus|haiku))?)"
    r"|(?:gemini(?:[-_. ]?(?:\d+(?:\.\d+)*|flash|pro))?)"
    r"|(?:deepseek(?:[-_. ]?[a-z0-9]+)?)"
    r"|(?:qwen(?:[-_. ]?[a-z0-9]+)?)"
    r"|(?:llama(?:[-_. ]?\d+(?:\.\d+)*)?)"
    r"|(?:mistral(?:[-_. ]?[a-z0-9]+)?)"
    r"|(?:perplexity|openai|anthropic|google)"
    r")(?:[-_. ]?(?:mini|turbo|preview|latest|r1|v?\d+(?:\.\d+)*))*$",
    re.IGNORECASE,
)

TASK_HINT_RE = re.compile(
    r"(写|生成|总结|翻译|分析|解释|润色|改写|整理|规划|设计|比较|推荐|提取|校对|制作|编写|"
    r"帮我|请你|如何|怎么|为什么|"
    r"write|draft|summarize|translate|analy[sz]e|explain|improve|create|build|help|how|why)",
    re.IGNORECASE,
)


def _looks_like_model_only_input(normalized: str, compact: str) -> bool:
    """判断输入是否基本只是在说模型名，而不是任务需求。"""
    if TASK_HINT_RE.search(normalized):
        return False

    # 限制在短语范围内，避免把正常长句误判
    token_count = len(normalized.split())
    if token_count == 0 or token_count > 4 or len(compact) > 40:
        return False

    return bool(MODEL_NAME_RE.fullmatch(normalized))


def _validate_user_input(user_input: str) -> str | None:
    """校验是否是可执行任务输入。返回错误文案或 None。"""
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", user_input.lower()).strip()
    if not normalized:
        return "请输入您的需求"

    compact = normalized.replace(" ", "")
    tokens = normalized.split()

    # 只输入模型名时，不进行推荐和提示词生成
    if _looks_like_model_only_input(normalized, compact):
        return (
            "你输入的是模型名，不是任务需求。"
            "请改为：你想让AI完成什么任务，例如“用Claude写一封求职邮件”。"
        )

    # 过短且缺少任务语义，提示用户补全需求
    if len(tokens) <= 1 and len(compact) <= 3:
        return "请描述具体任务，例如“帮我写一篇小红书文案”或“分析特斯拉商业模式”。"

    return None


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """分析用户需求，返回模型推荐和提示词"""
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["analyze_request"])
    if schema_err:
        return schema_err
    user_input = data.get("input", "").strip()

    if not user_input:
        return error_response(ERROR_CODES["BAD_REQUEST"], "请输入您的需求", 400)
    validation_error = _validate_user_input(user_input)
    if validation_error:
        return error_response(ERROR_CODES["BAD_REQUEST"], validation_error, 400)

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
    history_store.append(
        {
            "id": str(uuid.uuid4()),
            "input": user_input,
            "classification": response_data["classification"],
            "model_names": [r["model"]["name"] for r in results],
            "timestamp": time.time(),
        }
    )

    return jsonify(response_data)


@app.route("/api/workflow/start", methods=["POST"])
def workflow_start():
     """创建编排工作流会话。"""
     data = request.get_json() or {}
     schema_err = validate_json_payload(data, SCHEMAS["workflow_start_request"])
     if schema_err:
         return schema_err
     text = (data.get("text") or "").strip()
     if not text:
         return error_response(ERROR_CODES["BAD_REQUEST"], "text is required", 400)

     try:
         result = start_workflow(
             text=text,
             preferred_executor=data.get("preferred_executor"),
             context=data.get("context") or {},
         )
         # NOTE: Do NOT append to history here. History should only be added when task is completed.
         # This prevents incomplete/in-progress sessions from appearing in history.
         return jsonify(result)
     except Exception as exc:
         logger.exception("workflow start failed")
         return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)


@app.route("/api/workflow/clarify", methods=["POST"])
def workflow_clarify():
    """提交澄清答案，生成 spec 草案。"""
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_clarify_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    answers = data.get("answers") or {}
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)

    try:
        result = submit_clarifications(session_id=session_id, answers=answers)
        return jsonify(result)
    except KeyError as exc:
        return error_response(ERROR_CODES["SESSION_NOT_FOUND"], str(exc), 404)
    except ClarifyValidationError as exc:
        return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)
    except ValueError as exc:
        return error_response(ERROR_CODES["INVALID_STATE"], str(exc), 409)
    except Exception as exc:
        logger.exception("workflow clarify failed")
        return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)


@app.route("/api/workflow/confirm_spec", methods=["POST"])
def workflow_confirm_spec():
    """确认 spec 并生成路由与提示词。"""
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_confirm_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    spec = data.get("spec")
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)
    if not isinstance(spec, dict):
        return error_response(ERROR_CODES["BAD_REQUEST"], "spec is required", 400)

    try:
        result = confirm_spec(session_id=session_id, spec=spec)
        return jsonify(result)
    except KeyError as exc:
        return error_response(ERROR_CODES["SESSION_NOT_FOUND"], str(exc), 404)
    except ValueError as exc:
        return error_response(ERROR_CODES["INVALID_STATE"], str(exc), 409)
    except Exception as exc:
        logger.exception("workflow confirm_spec failed")
        return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)


@app.route("/api/workflow/execute", methods=["POST"])
def workflow_execute():
    """执行工作流。"""
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_execute_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    executor = data.get("executor", "prompt_only")
    executor_config = data.get("executor_config") or {}
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)

    idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()
    cache_key = f"execute:{idempotency_key}" if idempotency_key else ""
    cached = read_cached_response(cache_key) if cache_key else None
    if cached:
        return jsonify(cached)
    lock_token = acquire_lock(cache_key) if cache_key else None
    if cache_key and not lock_token:
        return error_response(ERROR_CODES["IDEMPOTENCY_CONFLICT"], "Duplicate execute request in progress. Please retry later.", 409)

    try:
        result = execute_session(
            session_id=session_id,
            executor=executor,
            executor_config=executor_config,
        )
        if idempotency_key:
            cache_response(cache_key, result)
        return jsonify(result)
    except KeyError as exc:
        return error_response(ERROR_CODES["SESSION_NOT_FOUND"], str(exc), 404)
    except ValueError as exc:
        return error_response(ERROR_CODES["INVALID_STATE"], str(exc), 409)
    except Exception as exc:
        logger.exception("workflow execute failed")
        return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)
    finally:
        if cache_key and lock_token:
            release_lock(cache_key)


@app.route("/api/v1/workflow/execute", methods=["POST"])
def workflow_execute_v1():
    if not ASYNC_JOB_AVAILABLE:
        return error_response(ERROR_CODES["INTERNAL_ERROR"], "Async job queue is unavailable.", 503)
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_execute_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    executor = data.get("executor", "prompt_only")
    executor_config = data.get("executor_config") or {}
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)

    job_id = enqueue_execute(session_id=session_id, executor=executor, executor_config=executor_config)
    return jsonify({"job_id": job_id, "state": "queued"}), 202


@app.route("/api/workflow/validate", methods=["POST"])
def workflow_validate():
    """校验执行输出，可选自动修订。"""
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_validate_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)

    idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()
    cache_key = f"validate:{idempotency_key}" if idempotency_key else ""
    cached = read_cached_response(cache_key) if cache_key else None
    if cached:
        return jsonify(cached)
    lock_token = acquire_lock(cache_key) if cache_key else None
    if cache_key and not lock_token:
        return error_response(ERROR_CODES["IDEMPOTENCY_CONFLICT"], "Duplicate validate request in progress. Please retry later.", 409)

    try:
        result = validate_session_output(
            session_id=session_id,
            output=data.get("output"),
            auto_revise=bool(data.get("auto_revise", False)),
        )
        if idempotency_key:
            cache_response(cache_key, result)
        return jsonify(result)
    except KeyError as exc:
        return error_response(ERROR_CODES["SESSION_NOT_FOUND"], str(exc), 404)
    except ValueError as exc:
        return error_response(ERROR_CODES["INVALID_STATE"], str(exc), 409)
    except Exception as exc:
        logger.exception("workflow validate failed")
        return error_response(ERROR_CODES["BAD_REQUEST"], str(exc), 400)
    finally:
        if cache_key and lock_token:
            release_lock(cache_key)


@app.route("/api/v1/workflow/validate", methods=["POST"])
def workflow_validate_v1():
    if not ASYNC_JOB_AVAILABLE:
        return error_response(ERROR_CODES["INTERNAL_ERROR"], "Async job queue is unavailable.", 503)
    data = request.get_json() or {}
    schema_err = validate_json_payload(data, SCHEMAS["workflow_validate_request"])
    if schema_err:
        return schema_err
    session_id = data.get("session_id")
    if not session_id:
        return error_response(ERROR_CODES["BAD_REQUEST"], "session_id is required", 400)
    output = data.get("output")
    auto_revise = bool(data.get("auto_revise", False))
    job_id = enqueue_validate(session_id=session_id, output=output, auto_revise=auto_revise)
    return jsonify({"job_id": job_id, "state": "queued"}), 202


@app.route("/api/v1/jobs/<job_id>", methods=["GET"])
def workflow_job_status_v1(job_id: str):
    if not ASYNC_JOB_AVAILABLE:
        return error_response(ERROR_CODES["INTERNAL_ERROR"], "Async job queue is unavailable.", 503)
    return jsonify(get_job(job_id))


@app.route("/api/health", methods=["GET"])
def health():
    """健康检查（含 LLM 状态）"""
    ollama_ok = llm_client.check_ollama()
    return jsonify({
        "status": "ok",
        "ollama_available": ollama_ok,
        "ollama_model": llm_client.OLLAMA_MODEL if ollama_ok else None,
    })


@app.route("/api/health/liveness", methods=["GET"])
def liveness():
    return jsonify({"status": "alive"}), 200


@app.route("/api/health/readiness", methods=["GET"])
def readiness():
    mysql_ok = mysql_available()
    redis_ok = redis_available()
    if mysql_ok:
        mysql_ok = bool(init_mysql_schema())
    ready = bool(redis_ok)
    return jsonify({
        "status": "ready" if ready else "degraded",
        "components": {
            "mysql_available": mysql_ok,
            "redis_available": redis_ok,
        },
    }), 200 if ready else 503


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/openapi.json", methods=["GET"])
def openapi_spec():
    return jsonify(OPENAPI_SPEC)


@app.route("/api/v1/workflow/start", methods=["POST"])
def workflow_start_v1():
    return workflow_start()


@app.route("/api/v1/workflow/clarify", methods=["POST"])
def workflow_clarify_v1():
    return workflow_clarify()


@app.route("/api/v1/workflow/confirm_spec", methods=["POST"])
def workflow_confirm_spec_v1():
    return workflow_confirm_spec()


# ============ History Routes ============
@app.route("/api/history", methods=["GET"])
def get_history():
    """获取历史记录列表。"""
    history = history_store.list()
    return jsonify({"history": history})


@app.route("/api/history/<history_id>", methods=["DELETE"])
def delete_history(history_id):
    """删除指定的历史记录。"""
    success = history_store.delete(history_id)
    if success:
        return jsonify({"success": True, "message": "History deleted"}), 200
    else:
        return error_response(ERROR_CODES["NOT_FOUND"], "History not found", 404)


# ============ V2 Orchestration Routes ============
try:
    from orchestrator.store import store
    init_orchestration_service(OrchestrationService(llm_client=llm_client, store=store))
    app.register_blueprint(orchestration_bp)
    logger.info("V2 orchestration routes registered at /api/v2")
except Exception as e:
    logger.warning(f"V2 orchestration routes not available: {e}")


if __name__ == "__main__":
    # 启动时检测 Gemini
    if llm_client.check_ollama():
        logger.info("Gemini 可用，将使用 LLM 进行智能分类和提示词生成")
    else:
        logger.warning("Gemini 不可用，将使用关键词匹配和模板生成（降级模式）")

    app.run(debug=True, port=5001)
