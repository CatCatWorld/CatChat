from __future__ import annotations

import os
import random
from typing import Any, Dict, List

from app.core.models import Phase, Role
from app.engine.game_engine import GameEngine


class PerspectiveEngine:
    """Build role-scoped view of game state for each cat agent."""

    PUBLIC_MEMORY_LIMIT = max(20, int(os.getenv("CAT_PUBLIC_MEMORY_LIMIT", "80")))
    SELF_MEMORY_LIMIT = max(10, int(os.getenv("CAT_SELF_MEMORY_LIMIT", "40")))
    WOLF_MEMORY_LIMIT = max(10, int(os.getenv("CAT_WOLF_MEMORY_LIMIT", "30")))
    RNG = random.SystemRandom()
    SENSITIVE_MARKERS_COMMON = {
        "今晚目标为",
        "今晚刀",
        "狼刀目标",
        "night target",
        "wolf_target",
        "wolf target",
        "guard_target",
        "witch_save",
        "witch_poison",
    }
    SENSITIVE_MARKERS_BY_ROLE = {
        Role.VILLAGER: {
            "seer_result",
            "is_wolf",
            "target_id",
            "wolf_team_ids",
            "wolf_team",
        },
        Role.GUARD: {
            "seer_result",
            "is_wolf",
            "target_id",
            "wolf_team_ids",
            "wolf_team",
        },
        Role.WITCH: {
            "seer_result",
            "is_wolf",
            "target_id",
            "wolf_team_ids",
            "wolf_team",
        },
        Role.HUNTER: {
            "seer_result",
            "is_wolf",
            "target_id",
            "wolf_team_ids",
            "wolf_team",
        },
        Role.FOOL: {
            "seer_result",
            "is_wolf",
            "target_id",
            "wolf_team_ids",
            "wolf_team",
        },
        Role.SEER: {
            "wolf_team_ids",
            "wolf_team",
        },
    }

    @staticmethod
    def build_visible_state(engine: GameEngine, player_id: str) -> Dict[str, Any]:
        snapshot = engine.snapshot
        player = snapshot.players[player_id]
        role = player.role
        ctx = snapshot.round_context

        alive_player_ids: List[str] = [
            p.player_id for p in snapshot.players.values() if p.alive
        ]
        dead_player_ids: List[str] = [
            p.player_id for p in snapshot.players.values() if not p.alive
        ]
        alive_player_ids = PerspectiveEngine._shuffled_player_ids(alive_player_ids)
        dead_player_ids = PerspectiveEngine._shuffled_player_ids(dead_player_ids)

        alive_players: List[str] = [
            PerspectiveEngine._player_name(snapshot.players.get(pid))
            for pid in alive_player_ids
        ]
        dead_players: List[str] = [
            PerspectiveEngine._player_name(snapshot.players.get(pid))
            for pid in dead_player_ids
        ]

        base: Dict[str, Any] = {
            "room_id": snapshot.room_id,
            "round_no": ctx.round_no,
            "phase": snapshot.phase.value,
            "player_id": player_id,
            "player_name": PerspectiveEngine._player_name(player),
            "alive_players": alive_players,
            "dead_players": dead_players,
            "alive_player_ids": alive_player_ids,
            "dead_player_ids": dead_player_ids,
            "target_candidates": [
                PerspectiveEngine._player_name(snapshot.players.get(pid))
                for pid in alive_player_ids
                if pid != player_id
            ],
            "public_deaths_this_round": {
                PerspectiveEngine._player_name(snapshot.players.get(pid)): PerspectiveEngine._death_cause_label(cause.value)
                for pid, cause in ctx.deaths_this_round.items()
            },
            "public_vote_log": PerspectiveEngine._extract_public_votes(
                snapshot.action_audit_log,
                snapshot.players,
            ),
            "your_identity_hint": PerspectiveEngine._identity_hint(role),
            "role_capability": {
                "can_use_antidote": role == Role.WITCH and not player.used_antidote,
                "can_use_poison": role == Role.WITCH and not player.used_poison,
                "can_hunter_shoot": role == Role.HUNTER and player.can_hunter_shoot,
            },
        }

        base["memory_context"] = PerspectiveEngine._build_memory_context(
            audit_log=snapshot.action_audit_log,
            players=snapshot.players,
            viewer_id=player_id,
            viewer_role=role,
            round_no=ctx.round_no,
            alive_count=len(alive_player_ids),
            dead_count=len(dead_player_ids),
        )

        if role == Role.WEREWOLF:
            base["wolf_team"] = [
                PerspectiveEngine._player_name(p)
                for p in snapshot.players.values()
                if p.alive and p.role == Role.WEREWOLF
            ]
            base["wolf_team_ids"] = [
                p.player_id
                for p in snapshot.players.values()
                if p.alive and p.role == Role.WEREWOLF
            ]

        if role == Role.WITCH and snapshot.phase == Phase.NIGHT_WITCH:
            base["wolf_target"] = PerspectiveEngine._player_name(
                snapshot.players.get(ctx.wolf_target) if ctx.wolf_target else None
            )
            base["wolf_target_id"] = ctx.wolf_target

        if role == Role.SEER:
            seer_result = engine.get_seer_result(player_id)
            if isinstance(seer_result, dict):
                target_id = seer_result.get("target")
                if isinstance(target_id, str):
                    seer_result = dict(seer_result)
                    seer_result["target_id"] = target_id
                    seer_result["target"] = PerspectiveEngine._player_name(
                        snapshot.players.get(target_id)
                    )
            base["seer_result"] = seer_result

        if role == Role.GUARD:
            base["last_guard_target"] = PerspectiveEngine._player_name(
                snapshot.players.get(player.last_guard_target)
                if player.last_guard_target
                else None
            )
            base["last_guard_target_id"] = player.last_guard_target

        return base

    @staticmethod
    def _shuffled_player_ids(player_ids: List[str]) -> List[str]:
        ids = list(player_ids)
        if len(ids) <= 1:
            return ids
        PerspectiveEngine.RNG.shuffle(ids)
        return ids

    @staticmethod
    def _extract_public_votes(
        audit_log: list[dict],
        players: dict,
    ) -> list[dict]:
        result: list[dict] = []
        for row in audit_log:
            if row.get("event_type") not in {"vote", "vote_result"}:
                continue
            payload = row.get("payload", {})
            actor_id = row.get("actor_id")
            target_id = payload.get("target") if isinstance(payload, dict) else None
            result.append(
                {
                    "event_type": row.get("event_type"),
                    "actor": PerspectiveEngine._player_name(players.get(actor_id)),
                    "target": PerspectiveEngine._player_name(players.get(target_id)),
                    "ts": row.get("ts"),
                }
            )
        return result[-50:]

    @staticmethod
    def _build_memory_context(
        audit_log: list[dict],
        players: dict,
        viewer_id: str,
        viewer_role: Role | None,
        round_no: int,
        alive_count: int,
        dead_count: int,
    ) -> dict:
        public_phases = {"day_announce", "day_discuss", "day_vote"}
        public_memory: list[dict] = []
        self_memory: list[dict] = []
        wolf_team_memory: list[dict] = []
        eliminated_players_public: list[str] = []
        last_vote_result: str = ""
        round_events_public: dict[int, list[str]] = {}
        current_round = 1
        seen_round_start = False

        for row in audit_log:
            event_type = str(row.get("event_type") or "")
            actor_id = str(row.get("actor_id") or "")
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            phase = str(payload.get("phase") or "")
            ts = row.get("ts")

            if event_type == "phase_change":
                changed_phase = str(payload.get("phase") or "")
                if changed_phase == Phase.NIGHT_WOLF.value:
                    if seen_round_start:
                        current_round += 1
                    else:
                        seen_round_start = True
                continue

            if event_type == "agent_speech":
                if actor_id == "god" and str(payload.get("role") or "") == "judge":
                    continue
                content = str(payload.get("content") or "").strip()
                if not content:
                    continue
                actor_name = PerspectiveEngine._player_name(players.get(actor_id))

                if phase in public_phases:
                    if PerspectiveEngine._should_block_public_memory_content(content, viewer_role):
                        continue
                    round_events_public.setdefault(current_round, []).append(content)
                    public_memory.append(
                        {
                            "phase": phase,
                            "speaker": actor_name,
                            "content": content,
                            "ts": ts,
                        }
                    )

                if actor_id == viewer_id:
                    self_memory.append(
                        {
                            "phase": phase,
                            "content": content,
                            "ts": ts,
                        }
                    )

                if viewer_role == Role.WEREWOLF and phase in {"night_wolf_discuss", "night_wolf"} and str(payload.get("role") or "") == Role.WEREWOLF.value:
                    wolf_team_memory.append(
                        {
                            "phase": phase,
                            "speaker": actor_name,
                            "content": content,
                            "ts": ts,
                        }
                    )
                continue

            if event_type == "god_narration":
                content = str(payload.get("content") or "").strip()
                narration_phase = str(payload.get("phase") or "")
                if content and narration_phase in public_phases:
                    if PerspectiveEngine._should_block_public_memory_content(content, viewer_role):
                        continue
                    round_events_public.setdefault(current_round, []).append(content)
                    public_memory.append(
                        {
                            "phase": narration_phase,
                            "speaker": "god",
                            "content": content,
                            "ts": ts,
                        }
                    )
                continue

            if event_type == "death":
                dead_id = str(payload.get("player_id") or "")
                if dead_id:
                    dead_name = PerspectiveEngine._player_name(players.get(dead_id))
                    cause = PerspectiveEngine._death_cause_label(str(payload.get("cause") or ""))
                    eliminated_players_public.append(dead_name)
                    round_events_public.setdefault(current_round, []).append(f"{dead_name} 出局（{cause}）。")
                    public_memory.append(
                        {
                            "phase": "day_announce",
                            "speaker": "system",
                            "content": f"{dead_name} 出局（{cause}）。",
                            "ts": ts,
                        }
                    )
                continue

            if event_type == "vote_result":
                result = str(payload.get("result") or "")
                if result == "exile":
                    target_id = str(payload.get("target") or "")
                    target_name = PerspectiveEngine._player_name(players.get(target_id))
                    text = f"白天投票结果：{target_name} 被放逐。"
                elif result == "tie_no_exile":
                    text = "白天投票结果：平票，无人出局。"
                elif result == "no_valid_vote":
                    text = "白天投票结果：未形成有效票型。"
                elif result == "fool_reveal_immune":
                    text = "白天投票结果：白痴翻牌免死。"
                else:
                    text = "白天投票已结算。"
                last_vote_result = text
                round_events_public.setdefault(current_round, []).append(text)
                public_memory.append(
                    {
                        "phase": "day_vote",
                        "speaker": "system",
                        "content": text,
                        "ts": ts,
                    }
                )
                continue

            if event_type == "fool_reveal":
                round_events_public.setdefault(current_round, []).append("白痴翻牌并免死，本轮无人出局。")
                public_memory.append(
                    {
                        "phase": "day_vote",
                        "speaker": "system",
                        "content": "白痴翻牌并免死，本轮无人出局。",
                        "ts": ts,
                    }
                )
                continue

            if event_type in {"vote", "night_action", "hunter_shot"} and actor_id == viewer_id:
                self_memory.append(
                    {
                        "phase": phase,
                        "content": f"你执行了 {event_type}。",
                        "ts": ts,
                    }
                )

        public_memory_limited = public_memory[-PerspectiveEngine.PUBLIC_MEMORY_LIMIT :]
        self_memory_limited = self_memory[-PerspectiveEngine.SELF_MEMORY_LIMIT :]
        highlights = PerspectiveEngine._dedupe_recent_public_memory(public_memory_limited, limit=12)
        round_summaries = PerspectiveEngine._build_round_summaries(round_events_public)
        rolling_summary = PerspectiveEngine._compose_rolling_summary(round_summaries)
        game_facts = {
            "public_event_count": len(public_memory),
            "self_event_count": len(self_memory),
            "alive_count": alive_count,
            "dead_count": dead_count,
            "eliminated_players": eliminated_players_public[-12:],
            "last_vote_result": last_vote_result,
            "recent_highlights": highlights,
            "round_summaries": round_summaries,
        }

        result = {
            "summary": PerspectiveEngine._compose_memory_summary(
                round_no=round_no,
                alive_count=alive_count,
                dead_count=dead_count,
                game_facts=game_facts,
            ),
            "public_memory": public_memory_limited,
            "self_memory": self_memory_limited,
            "game_facts": game_facts,
            "round_summaries": round_summaries,
            "rolling_summary": rolling_summary,
        }
        if viewer_role == Role.WEREWOLF:
            result["wolf_team_memory"] = wolf_team_memory[-PerspectiveEngine.WOLF_MEMORY_LIMIT :]
        return result

    @staticmethod
    def _dedupe_recent_public_memory(public_memory: list[dict], limit: int = 12) -> list[str]:
        highlights: list[str] = []
        seen: set[str] = set()
        for row in reversed(public_memory):
            content = str((row or {}).get("content") or "").strip()
            if not content:
                continue
            if content in seen:
                continue
            seen.add(content)
            highlights.append(content)
            if len(highlights) >= limit:
                break
        highlights.reverse()
        return highlights

    @staticmethod
    def _compose_memory_summary(
        round_no: int,
        alive_count: int,
        dead_count: int,
        game_facts: dict,
    ) -> str:
        parts = [
            f"当前第 {round_no} 轮，存活 {alive_count} 人，出局 {dead_count} 人。",
        ]
        eliminated = game_facts.get("eliminated_players") or []
        if eliminated:
            parts.append("已出局：" + "、".join(str(name) for name in eliminated[-6:]) + "。")
        last_vote = str(game_facts.get("last_vote_result") or "").strip()
        if last_vote:
            parts.append("最近一次投票结算：" + last_vote)
        highlights = game_facts.get("recent_highlights") or []
        if highlights:
            parts.append("近期关键记忆：" + " | ".join(str(item) for item in highlights[-5:]))
        return " ".join(parts)

    @staticmethod
    def _build_round_summaries(round_events_public: dict[int, list[str]], limit: int = 8) -> list[dict]:
        if not round_events_public:
            return []
        result: list[dict] = []
        for round_no in sorted(round_events_public.keys()):
            events = [str(item).strip() for item in round_events_public.get(round_no, []) if str(item).strip()]
            if not events:
                continue
            deduped = []
            seen = set()
            for text in events:
                if text in seen:
                    continue
                seen.add(text)
                deduped.append(text)
            highlights = deduped[-4:]
            summary = "；".join(highlights)
            result.append(
                {
                    "round_no": round_no,
                    "event_count": len(deduped),
                    "highlights": highlights,
                    "summary": summary,
                }
            )
        return result[-limit:]

    @staticmethod
    def _compose_rolling_summary(round_summaries: list[dict], limit: int = 4) -> str:
        if not round_summaries:
            return ""
        items = round_summaries[-limit:]
        parts = []
        for item in items:
            round_no = item.get("round_no")
            summary = str(item.get("summary") or "").strip()
            if not summary:
                continue
            parts.append(f"第{round_no}轮：{summary}")
        return " | ".join(parts)

    @staticmethod
    def _should_block_public_memory_content(content: str, viewer_role: Role | None) -> bool:
        text = str(content or "").strip().lower()
        if not text:
            return False
        sensitive_markers = set(PerspectiveEngine.SENSITIVE_MARKERS_COMMON)
        if viewer_role in PerspectiveEngine.SENSITIVE_MARKERS_BY_ROLE:
            sensitive_markers.update(PerspectiveEngine.SENSITIVE_MARKERS_BY_ROLE.get(viewer_role) or set())
        return any(str(marker).lower() in text for marker in sensitive_markers)

    @staticmethod
    def _player_name(player: Any) -> str:
        if not player:
            return "unknown"
        nickname = getattr(player, "nickname", None)
        player_id = getattr(player, "player_id", None)
        return str(nickname or player_id or "unknown")

    @staticmethod
    def _identity_hint(role: Role | None) -> str:
        mapping = {
            Role.WEREWOLF: "你每晚可与狼队友协同刀人，白天需隐藏身份。",
            Role.VILLAGER: "你是普通村民，依靠发言与投票找狼。",
            Role.SEER: "你每晚可查验一人身份（是否狼人）。",
            Role.WITCH: "你有一瓶解药和一瓶毒药，各只能使用一次。",
            Role.HUNTER: "你被狼杀或放逐时可开枪带走一人（被毒杀不可开枪）。",
            Role.GUARD: "你每晚可守护一人，不能连续两晚守同一人。",
            Role.FOOL: "你被白天放逐时会翻牌免死一次，但之后失去投票权。",
        }
        return mapping.get(role, "保持理性分析并遵守规则。")

    @staticmethod
    def _death_cause_label(cause: str) -> str:
        mapping = {
            "wolf": "被狼人袭击",
            "poison": "被女巫毒杀",
            "vote": "被投票放逐",
            "hunter": "被猎人带走",
        }
        return mapping.get(str(cause or "").lower(), str(cause or "未知原因"))
