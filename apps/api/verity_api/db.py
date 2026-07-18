import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


DB_PATH = Path(__file__).resolve().parents[1] / "verity.db"

DATA_SOURCE = {
    "mode": "local-db",
    "seed": "mock",
    "is_real_workflow": False,
    "note": "Phase 2 reads mock-seeded product data from local SQLite. It is not real online collection.",
}


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                competitors_json TEXT NOT NULL,
                evidence_count INTEGER NOT NULL DEFAULT 0,
                claim_count INTEGER NOT NULL DEFAULT 0,
                high_confidence_count INTEGER NOT NULL DEFAULT 0,
                qa_status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data_source TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expert_agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                layer TEXT NOT NULL,
                role TEXT NOT NULL,
                tool_scope_json TEXT NOT NULL,
                output_schema TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence_items (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                source_type TEXT NOT NULL,
                platform TEXT NOT NULL,
                source_label TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                retrieval_status TEXT NOT NULL,
                claim_types_json TEXT NOT NULL,
                summary TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                confidence_level TEXT NOT NULL,
                scores_json TEXT NOT NULL,
                risk_note TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL,
                strength TEXT NOT NULL,
                dimension TEXT NOT NULL,
                evidence_ids_json TEXT NOT NULL,
                risk_note TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS analysis_packs (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS qa_gate_results (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                verdict TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                scores_json TEXT NOT NULL,
                hard_failures_json TEXT NOT NULL,
                issues_json TEXT NOT NULL,
                recommendations_json TEXT NOT NULL,
                rework_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS trace_steps (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                agent TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                token_count INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                evidence_ids_json TEXT NOT NULL,
                report_sections_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS annotations (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                target_text TEXT NOT NULL,
                kind TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE TABLE IF NOT EXISTS research_memories (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                status TEXT NOT NULL,
                content TEXT NOT NULL,
                source_report_id TEXT,
                confidence INTEGER NOT NULL,
                risk_note TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_label TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        _ensure_memory_columns(connection)
        seed_if_empty(connection)
        seed_knowledge_if_empty(connection)


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _ensure_memory_columns(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(research_memories)").fetchall()}
    additions = {
        "target_agent": "TEXT NOT NULL DEFAULT ''",
        "influence_target": "TEXT NOT NULL DEFAULT ''",
        "source_type": "TEXT NOT NULL DEFAULT ''",
        "source_ref": "TEXT NOT NULL DEFAULT ''",
        "evidence_json": "TEXT NOT NULL DEFAULT '[]'",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
        "applied_count": "INTEGER NOT NULL DEFAULT 0",
        "trial_count": "INTEGER NOT NULL DEFAULT 0",
        "positive_signal_count": "INTEGER NOT NULL DEFAULT 0",
        "negative_signal_count": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, definition in additions.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE research_memories ADD COLUMN {column} {definition}")


def _load_json(row: sqlite3.Row, key: str):
    return json.loads(row[key])


def seed_if_empty(connection: sqlite3.Connection) -> None:
    report_count = connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    if report_count:
        return

    reports = [
        (
            "mock-001",
            "AI 协作写作竞品分析",
            "比较 AI 协作写作场景下的定位、定价和用户声音。",
            ["Notion AI", "飞书妙记", "Gamma"],
            3,
            3,
            2,
            "pass",
            "2026-07-10",
            "mock-seed",
        ),
        (
            "mock-002",
            "B2B SaaS 定价策略研究",
            "识别免费层、团队版边界和企业版销售线索。",
            ["Linear", "Jira", "Asana"],
            0,
            0,
            0,
            "risk",
            "2026-07-09",
            "mock-seed",
        ),
        (
            "mock-003",
            "生成式演示工具定位研究",
            "比较从零生成、模板编辑和团队协作的差异。",
            ["Gamma", "Tome", "Canva AI"],
            0,
            0,
            0,
            "draft",
            "2026-07-08",
            "mock-seed",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO reports (
            id, title, summary, competitors_json, evidence_count, claim_count,
            high_confidence_count, qa_status, updated_at, data_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(report[0], report[1], report[2], _json(report[3]), *report[4:]) for report in reports],
    )

    experts = [
        (
            "orchestrator",
            "Research Orchestrator",
            "decision",
            "理解任务、拆解计划、选择专家、管理状态并汇总结果。",
            ["workflow", "trace", "expert_router"],
            "research_plan",
        ),
        (
            "evidence-collector",
            "Evidence Collector",
            "execution",
            "采集公开网页、用户 URL 和上传材料，输出结构化 Evidence。",
            ["web_fetch", "file_to_text"],
            "evidence_items",
        ),
        (
            "qa-agent",
            "QA Agent",
            "strategy",
            "检查 Analysis Pack 的证据充分性、结论可信度和数据缺口。",
            ["qa_gate", "trace"],
            "qa_gate_result",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO expert_agents (
            id, name, layer, role, tool_scope_json, output_schema
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(expert[0], expert[1], expert[2], expert[3], _json(expert[4]), expert[5]) for expert in experts],
    )

    evidence_items = [
        (
            "ev_mock_001",
            "mock-001",
            "Notion AI Pricing Page",
            "https://www.notion.so/product/ai",
            "official",
            "notion",
            "官网 · 可复查 · Mock timestamp",
            "2026-07-10",
            "success",
            ["pricing"],
            "官网价格页，来源权威、可复查。真实接入后需要重新校验时效性与套餐内容。",
            86,
            "high",
            {
                "source_authority": 19,
                "relevance": 18,
                "verifiability": 14,
                "freshness": 9,
                "specificity": 13,
                "corroboration": 7,
                "risk_penalty": 4,
            },
            "价格可能随地区或时间变化，需要定期刷新。",
        ),
        (
            "ev_mock_002",
            "mock-001",
            "Gamma Product Page",
            "https://gamma.app",
            "official",
            "gamma",
            "公开网页 · Mock source",
            "2026-07-10",
            "success",
            ["positioning", "feature"],
            "支撑“展示型内容生成”定位判断。真实接入后点击会打开原始链接或用户上传材料。",
            84,
            "high",
            {
                "source_authority": 18,
                "relevance": 18,
                "verifiability": 13,
                "freshness": 9,
                "specificity": 12,
                "corroboration": 8,
                "risk_penalty": 4,
            },
            "页面为产品介绍，部分差异化判断仍需用户反馈或第三方资料交叉验证。",
        ),
        (
            "ev_mock_003",
            "mock-001",
            "User Voice Sample",
            "#mock-user-voice",
            "sample",
            "mock",
            "示例数据 · 样本不足",
            "2026-07-10",
            "sample",
            ["user_voice"],
            "只允许作为风险提示，不支撑强结论。可加入知识库，但不自动写入 active memory。",
            63,
            "medium",
            {
                "source_authority": 8,
                "relevance": 15,
                "verifiability": 6,
                "freshness": 7,
                "specificity": 10,
                "corroboration": 3,
                "risk_penalty": 6,
            },
            "样本量不足，且不代表全网舆情。",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO evidence_items (
            id, report_id, title, url, source_type, platform, source_label,
            captured_at, retrieval_status, claim_types_json, summary, confidence,
            confidence_level, scores_json, risk_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
                item[6],
                item[7],
                item[8],
                _json(item[9]),
                item[10],
                item[11],
                item[12],
                _json(item[13]),
                item[14],
            )
            for item in evidence_items
        ],
    )

    claims = [
        (
            "claim_mock_001",
            "mock-001",
            "Notion AI 更适合作为已有知识库和文档协作流程中的增量能力。",
            "supported",
            "strong",
            "产品定位",
            ["ev_mock_001"],
            "当前仅由 mock seed 支撑，真实接入后需重新采集官方页面。",
        ),
        (
            "claim_mock_002",
            "mock-001",
            "Gamma 的核心差异更接近展示型内容生成，而不是完整知识库协作。",
            "supported",
            "strong",
            "核心场景",
            ["ev_mock_002"],
            "需要补充用户实际使用反馈来验证场景边界。",
        ),
        (
            "claim_mock_003",
            "mock-001",
            "用户声音显示团队协作体验存在分歧。",
            "weakly_supported",
            "weak",
            "用户声音",
            ["ev_mock_003"],
            "样本不足，只能作为风险提示，不能写成强结论。",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO claims (
            id, report_id, text, status, strength, dimension, evidence_ids_json, risk_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(claim[0], claim[1], claim[2], claim[3], claim[4], claim[5], _json(claim[6]), claim[7]) for claim in claims],
    )

    analysis_pack = {
        "research_goal": "分析 Notion AI、飞书妙记、Gamma 在 AI 协作写作场景下的产品策略、定价与用户反馈差异",
        "claims": [claim[0] for claim in claims],
        "evidence_items": [item[0] for item in evidence_items],
        "data_gaps": ["用户声音样本不足，不能声称全网舆情。"],
        "conflicts": [],
        "ready_for_qa": True,
    }
    connection.execute(
        """
        INSERT INTO analysis_packs (id, report_id, payload_json, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("ap_mock_001", "mock-001", _json(analysis_pack), "2026-07-10T20:00:00+08:00"),
    )

    connection.execute(
        """
        INSERT INTO qa_gate_results (
            id, report_id, verdict, total_score, scores_json, hard_failures_json,
            issues_json, recommendations_json, rework_count, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "qa_mock_001",
            "mock-001",
            "pass",
            82,
            _json(
                {
                    "evidence_sufficiency": 80,
                    "dimension_coverage": 84,
                    "claim_reliability": 82,
                    "structured_completeness": 88,
                    "evidence_consistency": 86,
                    "data_gap_risk": 72,
                }
            ),
            _json([]),
            _json(["用户声音样本不足，报告中必须降级表述。"]),
            _json(["将用户声音章节写为风险提示，不写成确定性市场判断。"]),
            0,
            "2026-07-10T20:02:00+08:00",
        ),
    )

    trace_steps = [
        (
            "trace_mock_001",
            "mock-001",
            "Plan",
            "Research Orchestrator",
            "将用户目标拆解为证据采集、产品分析、定价分析和用户声音分析。",
            "done",
            "mock-model",
            "Mock prompt placeholder. No sensitive input is stored.",
            {"goal": analysis_pack["research_goal"]},
            {"tasks": ["evidence", "product", "pricing", "user_voice"]},
            420,
            5200,
            [],
            ["scope", "plan"],
            "2026-07-10T20:00:20+08:00",
        ),
        (
            "trace_mock_002",
            "mock-001",
            "QA Gate",
            "QA Agent",
            "检查 Analysis Pack 的证据充分性、结论可信度和数据缺口。",
            "rework",
            "mock-model",
            "Mock QA checklist prompt. No raw secret is stored.",
            {"analysis_pack_id": "ap_mock_001"},
            {"issue": "用户声音章节有强结论风险，需要降级。"},
            360,
            3700,
            ["ev_mock_003"],
            ["user_voice"],
            "2026-07-10T20:02:00+08:00",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO trace_steps (
            id, report_id, stage, agent, task, status, model, prompt, input_json,
            output_json, token_count, duration_ms, evidence_ids_json,
            report_sections_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                step[0],
                step[1],
                step[2],
                step[3],
                step[4],
                step[5],
                step[6],
                step[7],
                _json(step[8]),
                _json(step[9]),
                step[10],
                step[11],
                _json(step[12]),
                _json(step[13]),
                step[14],
            )
            for step in trace_steps
        ],
    )


def seed_knowledge_if_empty(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
    if count:
        return
    connection.execute(
        """
        INSERT INTO knowledge_items (id, title, content, source_label, tags_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "kn_mock_pricing_token_value",
            "大模型价格分析应比较 token 可用量",
            "分析大模型价格时，不能只比较订阅价格或 API 标价，还应比较同预算下的 input/output token 可用量、调用次数、上下文长度、速率限制、免费额度和套餐权益。",
            "用户知识库 · 示例条目",
            _json(["pricing", "llm", "token", "agent_lesson_candidate"]),
            "2026-07-11T00:00:00+08:00",
        ),
    )


def list_reports() -> list[dict]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM reports ORDER BY updated_at DESC").fetchall()
    return [_report_from_row(row) for row in rows]


def get_report(report_id: str) -> dict | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return _report_from_row(row) if row else None


def list_experts() -> list[dict]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM expert_agents ORDER BY rowid").fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "layer": row["layer"],
            "role": row["role"],
            "tool_scope": _load_json(row, "tool_scope_json"),
            "output_schema": row["output_schema"],
        }
        for row in rows
    ]


def list_evidence(report_id: str | None = None) -> list[dict]:
    init_db()
    query = "SELECT * FROM evidence_items"
    params: tuple[str, ...] = ()
    if report_id:
        query += " WHERE report_id = ?"
        params = (report_id,)
    query += " ORDER BY rowid"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_evidence_from_row(row) for row in rows]


def list_knowledge_items() -> list[dict]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM knowledge_items ORDER BY rowid DESC").fetchall()
    return [_knowledge_from_row(row) for row in rows]


def cite_knowledge_as_evidence(report_id: str, knowledge_id: str) -> dict | None:
    init_db()
    with get_connection() as connection:
        knowledge = connection.execute("SELECT * FROM knowledge_items WHERE id = ?", (knowledge_id,)).fetchone()
        if not knowledge:
            return None
        evidence_id = f"ev_knowledge_{knowledge_id}_{report_id}"
        connection.execute(
            """
            INSERT OR REPLACE INTO evidence_items (
                id, report_id, title, url, source_type, platform, source_label,
                captured_at, retrieval_status, claim_types_json, summary, confidence,
                confidence_level, scores_json, risk_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                report_id,
                knowledge["title"],
                f"#knowledge-{knowledge_id}",
                "user_knowledge",
                "knowledge_base",
                knowledge["source_label"],
                "2026-07-11",
                "knowledge_cited",
                _json(["user_knowledge"]),
                knowledge["content"],
                72,
                "medium",
                _json(
                    {
                        "source_authority": 10,
                        "relevance": 16,
                        "verifiability": 9,
                        "freshness": 7,
                        "specificity": 13,
                        "corroboration": 4,
                        "risk_penalty": 2,
                    }
                ),
                "来自用户知识库，可作为本次研究的内部资料源；不能自动成为 active memory。",
            ),
        )
        count = connection.execute("SELECT COUNT(*) FROM evidence_items WHERE report_id = ?", (report_id,)).fetchone()[0]
        high_count = connection.execute("SELECT COUNT(*) FROM evidence_items WHERE report_id = ? AND confidence_level = 'high'", (report_id,)).fetchone()[0]
        connection.execute("UPDATE reports SET evidence_count = ?, high_confidence_count = ? WHERE id = ?", (count, high_count, report_id))
    return next((item for item in list_evidence(report_id) if item["id"] == evidence_id), None)


def list_claims(report_id: str) -> list[dict]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM claims WHERE report_id = ? ORDER BY rowid", (report_id,)).fetchall()
    return [
        {
            "id": row["id"],
            "report_id": row["report_id"],
            "text": row["text"],
            "status": row["status"],
            "strength": row["strength"],
            "dimension": row["dimension"],
            "evidence_ids": _load_json(row, "evidence_ids_json"),
            "risk_note": row["risk_note"],
        }
        for row in rows
    ]


def list_trace_steps(report_id: str) -> list[dict]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM trace_steps WHERE report_id = ? ORDER BY rowid", (report_id,)).fetchall()
    return [
        {
            "id": row["id"],
            "report_id": row["report_id"],
            "stage": row["stage"],
            "agent": row["agent"],
            "task": row["task"],
            "status": row["status"],
            "model": row["model"],
            "prompt": row["prompt"],
            "input": _load_json(row, "input_json"),
            "output": _load_json(row, "output_json"),
            "token_count": row["token_count"],
            "duration_ms": row["duration_ms"],
            "evidence_ids": _load_json(row, "evidence_ids_json"),
            "report_sections": _load_json(row, "report_sections_json"),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def create_memory_candidate(
    *,
    memory_type: str,
    content: str,
    target_agent: str,
    influence_target: str,
    source_type: str,
    source_report_id: str | None = None,
    source_ref: str = "",
    evidence: list[str] | None = None,
    confidence: int = 70,
    risk_note: str = "",
    status: str = "candidate",
) -> dict:
    init_db()
    memory_id = f"mem_{uuid4().hex[:12]}"
    now = "2026-07-11T00:00:00+08:00"
    normalized_status = _memory_status(memory_type, status, confidence, content, influence_target, risk_note)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO research_memories (
                id, memory_type, status, content, source_report_id, confidence, risk_note,
                created_at, target_agent, influence_target, source_type, source_ref,
                evidence_json, updated_at, applied_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                memory_type,
                normalized_status,
                content,
                source_report_id,
                confidence,
                risk_note,
                now,
                target_agent,
                influence_target,
                source_type,
                source_ref,
                _json(evidence or []),
                now,
                0,
            ),
        )
    return get_memory(memory_id) or {}


def list_memories(status: str | None = None, target_agent: str | None = None) -> list[dict]:
    init_db()
    query = "SELECT * FROM research_memories"
    clauses = []
    params: list[str] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if target_agent:
        clauses.append("target_agent = ?")
        params.append(target_agent)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY rowid DESC"
    with get_connection() as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return [_memory_from_row(row) for row in rows]


def get_memory(memory_id: str) -> dict | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM research_memories WHERE id = ?", (memory_id,)).fetchone()
    return _memory_from_row(row) if row else None


def update_memory_status(memory_id: str, status: str) -> dict | None:
    if status not in {"candidate", "draft", "active", "quarantined", "archived"}:
        raise ValueError(f"invalid memory status: {status}")
    item = get_memory(memory_id)
    if not item:
        return None
    normalized = _memory_status(
        item["memory_type"],
        status,
        item["confidence"],
        item["content"],
        item["influence_target"],
        item["risk_note"],
    )
    now = "2026-07-11T00:00:00+08:00"
    with get_connection() as connection:
        connection.execute("UPDATE research_memories SET status = ?, updated_at = ? WHERE id = ?", (normalized, now, memory_id))
    return get_memory(memory_id)


def list_active_memories_for_agent(target_agent: str, limit: int = 3) -> list[dict]:
    return list_memories(status="active", target_agent=target_agent)[:limit]


def list_candidate_memories_for_agent(target_agent: str, limit: int = 2) -> list[dict]:
    return list_memories(status="candidate", target_agent=target_agent)[:limit]


def increment_memory_applied(memory_ids: list[str]) -> None:
    if not memory_ids:
        return
    init_db()
    with get_connection() as connection:
        connection.executemany("UPDATE research_memories SET applied_count = applied_count + 1 WHERE id = ?", [(memory_id,) for memory_id in memory_ids])


def increment_memory_trial(memory_ids: list[str]) -> None:
    if not memory_ids:
        return
    init_db()
    with get_connection() as connection:
        connection.executemany("UPDATE research_memories SET trial_count = trial_count + 1 WHERE id = ?", [(memory_id,) for memory_id in memory_ids])


def record_memory_signal(memory_id: str, signal: str) -> dict | None:
    if signal not in {"positive", "negative"}:
        raise ValueError(f"invalid memory signal: {signal}")
    column = "positive_signal_count" if signal == "positive" else "negative_signal_count"
    init_db()
    with get_connection() as connection:
        connection.execute(f"UPDATE research_memories SET {column} = {column} + 1 WHERE id = ?", (memory_id,))
        if signal == "negative":
            connection.execute("UPDATE research_memories SET status = 'quarantined' WHERE id = ?", (memory_id,))
    return get_memory(memory_id)


def _memory_status(memory_type: str, requested_status: str, confidence: int, content: str, influence_target: str, risk_note: str) -> str:
    if requested_status == "active":
        if confidence < 70:
            return "quarantined"
        if not content.strip() or not influence_target.strip():
            return "quarantined"
        if memory_type in {"competitor_fact", "validated_insight", "research_pattern"}:
            return "candidate"
        lowered_risk = risk_note.lower()
        if any(marker in lowered_risk for marker in ["低可信", "冲突", "过期", "不可复查", "sensitive"]):
            return "quarantined"
    return requested_status


def replace_trace_steps(report_id: str, steps: list[dict[str, Any]], *, source_prefix: str = "") -> int:
    init_db()
    with get_connection() as connection:
        if source_prefix:
            connection.execute("DELETE FROM trace_steps WHERE report_id = ? AND id LIKE ?", (report_id, f"{source_prefix}%"))
        else:
            connection.execute("DELETE FROM trace_steps WHERE report_id = ?", (report_id,))
        connection.executemany(
            """
            INSERT INTO trace_steps (
                id, report_id, stage, agent, task, status, model, prompt, input_json,
                output_json, token_count, duration_ms, evidence_ids_json,
                report_sections_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    step["id"],
                    report_id,
                    step["stage"],
                    step["agent"],
                    step["task"],
                    step["status"],
                    step["model"],
                    step["prompt"],
                    _json(step["input"]),
                    _json(step["output"]),
                    step["token_count"],
                    step["duration_ms"],
                    _json(step["evidence_ids"]),
                    _json(step["report_sections"]),
                    step["created_at"],
                )
                for step in steps
            ],
        )
    return len(steps)


def append_trace_step(report_id: str, step: dict[str, Any]) -> None:
    """Append one trace step without replacing an existing workflow trace."""
    init_db()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO trace_steps (
                id, report_id, stage, agent, task, status, model, prompt, input_json,
                output_json, token_count, duration_ms, evidence_ids_json,
                report_sections_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step["id"],
                report_id,
                step["stage"],
                step["agent"],
                step["task"],
                step["status"],
                step["model"],
                step["prompt"],
                _json(step["input"]),
                _json(step["output"]),
                step["token_count"],
                step["duration_ms"],
                _json(step["evidence_ids"]),
                _json(step["report_sections"]),
                step["created_at"],
            ),
        )


def persist_bounded_workflow_result(
    *,
    report_id: str,
    title: str,
    research_goal: str,
    competitors: list[str],
    evidence_items: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    analysis_pack: dict[str, Any],
    qa_result: dict[str, Any],
    updated_at: str,
) -> None:
    """Persist a WorkflowEngine validation run without relabelling it as online research."""
    init_db()
    with get_connection() as connection:
        for table in ("evidence_items", "claims", "analysis_packs", "qa_gate_results"):
            connection.execute(f"DELETE FROM {table} WHERE report_id = ?", (report_id,))
        connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        connection.execute(
            """
            INSERT INTO reports (
                id, title, summary, competitors_json, evidence_count, claim_count,
                high_confidence_count, qa_status, updated_at, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                title,
                research_goal,
                _json(competitors),
                len(evidence_items),
                len(claims),
                sum(item["confidence_level"] == "high" for item in evidence_items),
                qa_result["verdict"],
                updated_at,
                "evolva-workflow-local-evidence",
            ),
        )
        connection.executemany(
            """
            INSERT INTO evidence_items (
                id, report_id, title, url, source_type, platform, source_label,
                captured_at, retrieval_status, claim_types_json, summary, confidence,
                confidence_level, scores_json, risk_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["id"], report_id, item["title"], item.get("url") or item.get("file_source"),
                    item["source_type"], item["platform"], "本地受控证据 · Evolva WorkflowEngine",
                    item["captured_at"], item["retrieval_status"], _json(item["claim_types"]),
                    item["summary"], item["confidence"], item["confidence_level"],
                    _json(item["scores"]), item["risk_note"],
                )
                for item in evidence_items
            ],
        )
        connection.executemany(
            """
            INSERT INTO claims (
                id, report_id, text, status, strength, dimension, evidence_ids_json, risk_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (claim["id"], report_id, claim["text"], claim["status"], claim["strength"],
                 claim["dimension"], _json(claim["evidence_ids"]), claim["risk_note"])
                for claim in claims
            ],
        )
        connection.execute(
            "INSERT INTO analysis_packs (id, report_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (f"ap_{report_id}", report_id, _json(analysis_pack), updated_at),
        )
        connection.execute(
            """
            INSERT INTO qa_gate_results (
                id, report_id, verdict, total_score, scores_json, hard_failures_json,
                issues_json, recommendations_json, rework_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"qa_{report_id}", report_id, qa_result["verdict"], qa_result["total_score"],
                _json(qa_result["scores"]), _json(qa_result["hard_failures"]),
                _json(qa_result["issues"]), _json(qa_result["recommendations"]),
                qa_result["rework_count"], updated_at,
            ),
        )


def get_qa_result(report_id: str) -> dict | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM qa_gate_results WHERE report_id = ? ORDER BY created_at DESC LIMIT 1",
            (report_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "report_id": row["report_id"],
        "verdict": row["verdict"],
        "total_score": row["total_score"],
        "scores": _load_json(row, "scores_json"),
        "hard_failures": _load_json(row, "hard_failures_json"),
        "issues": _load_json(row, "issues_json"),
        "recommendations": _load_json(row, "recommendations_json"),
        "rework_count": row["rework_count"],
        "created_at": row["created_at"],
    }


def _report_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "summary": row["summary"],
        "competitors": _load_json(row, "competitors_json"),
        "evidence_count": row["evidence_count"],
        "claim_count": row["claim_count"],
        "high_confidence_count": row["high_confidence_count"],
        "qa_status": row["qa_status"],
        "updated_at": row["updated_at"],
        "data_source": row["data_source"],
    }


def _evidence_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "report_id": row["report_id"],
        "title": row["title"],
        "url": row["url"],
        "source_type": row["source_type"],
        "platform": row["platform"],
        "source": row["source_label"],
        "captured_at": row["captured_at"],
        "retrieval_status": row["retrieval_status"],
        "claim_types": _load_json(row, "claim_types_json"),
        "summary": row["summary"],
        "confidence": row["confidence"],
        "confidence_level": row["confidence_level"],
        "level": row["confidence_level"],
        "scores": _load_json(row, "scores_json"),
        "risk_note": row["risk_note"],
    }


def _memory_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "memory_type": row["memory_type"],
        "status": row["status"],
        "content": row["content"],
        "source_report_id": row["source_report_id"],
        "confidence": row["confidence"],
        "risk_note": row["risk_note"],
        "created_at": row["created_at"],
        "target_agent": row["target_agent"],
        "influence_target": row["influence_target"],
        "effect_strategy": row["influence_target"],
        "source_type": row["source_type"],
        "source_ref": row["source_ref"],
        "evidence": _load_json(row, "evidence_json"),
        "updated_at": row["updated_at"],
        "applied_count": row["applied_count"],
        "trial_count": row["trial_count"],
        "positive_signal_count": row["positive_signal_count"],
        "negative_signal_count": row["negative_signal_count"],
    }


def _knowledge_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "source_label": row["source_label"],
        "tags": _load_json(row, "tags_json"),
        "created_at": row["created_at"],
    }
