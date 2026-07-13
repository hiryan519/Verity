from verity_api.expert_instance_planner import merge_instance_fragments, plan_expert_instances


def test_plan_splits_multi_instance_expert_by_token_budget() -> None:
    plans = plan_expert_instances(
        expert_id="product_analyst",
        token_budget=100,
        work_units=[
            {"id": "slice_1", "topic": "产品定位", "token_estimate": 80, "evidence_ids": ["ev_1"]},
            {"id": "slice_2", "topic": "功能边界", "token_estimate": 70, "evidence_ids": ["ev_2"]},
        ],
    )

    assert len(plans) == 2
    assert all(plan["expert_id"] == "product_analyst" for plan in plans)
    assert plans[0]["split_reason"] == "token_budget"
    assert plans[0]["evidence_ids"] == ["ev_1"]
    assert plans[1]["evidence_ids"] == ["ev_2"]


def test_plan_splits_by_unit_count_without_pretending_more_agents_are_always_needed() -> None:
    plans = plan_expert_instances(
        expert_id="cross_validator",
        token_budget=10_000,
        max_units_per_instance=2,
        work_units=[
            {"id": "check_1", "topic": "产品内部", "claim_ids": ["c1"]},
            {"id": "check_2", "topic": "定价内部", "claim_ids": ["c2"]},
            {"id": "check_3", "topic": "产品 x 定价", "claim_ids": ["c3"]},
        ],
    )

    assert len(plans) == 2
    assert plans[0]["split_reason"] == "unit_count"
    assert plans[1]["split_reason"] == "unit_count"
    assert plans[0]["claim_ids"] == ["c1", "c2"]
    assert plans[1]["claim_ids"] == ["c3"]


def test_plan_keeps_single_instance_for_non_multi_instance_expert() -> None:
    plans = plan_expert_instances(
        expert_id="qa_agent",
        token_budget=100,
        work_units=[
            {"id": "qa_1", "topic": "QA Brief A", "token_estimate": 80},
            {"id": "qa_2", "topic": "QA Brief B", "token_estimate": 80},
        ],
    )

    assert len(plans) == 1
    assert plans[0]["split_reason"] == "forced_single"
    assert len(plans[0]["work_units"]) == 2


def test_merge_instance_fragments_preserves_traceability_and_risks() -> None:
    merged = merge_instance_fragments(
        expert_id="product_analyst",
        output_pack_type="Product Analysis Pack",
        fragments=[
            {
                "instance_id": "product_analyst_a",
                "scope": "产品定位",
                "evidence_ids": ["ev_1"],
                "claim_ids": ["c1"],
                "output": {
                    "claims": [{"claim_id": "c1", "claim_text": "A"}],
                    "data_gaps": ["缺少帮助文档"],
                    "risk_notes": ["官网宣传需降级"],
                },
            },
            {
                "instance_id": "product_analyst_b",
                "scope": "功能边界",
                "evidence_ids": ["ev_2", "ev_1"],
                "claim_ids": ["c2"],
                "output": {
                    "claims": [{"claim_id": "c2", "claim_text": "B"}],
                    "data_gaps": ["缺少帮助文档"],
                    "risk_notes": ["功能页证据不足"],
                },
            },
        ],
    )

    assert merged["pack_type"] == "Product Analysis Pack"
    assert merged["fragment_count"] == 2
    assert merged["evidence_ids"] == ["ev_1", "ev_2"]
    assert merged["claim_ids"] == ["c1", "c2"]
    assert merged["data_gaps"] == ["缺少帮助文档"]
    assert merged["risk_notes"] == ["官网宣传需降级", "功能页证据不足"]
    assert merged["fragment_index"][0]["merge_reason"] == "merged_same_expert_fragment"
