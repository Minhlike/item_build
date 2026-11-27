from collections import Counter
from math import isfinite
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .catalog import eligibility
from .models import Id, Integer, Model, Nonempty, Nonnegative
from .retrieval import LANES, Repository

Ratio = Annotated[Nonnegative, Field(le=1)]
Horizon = Literal["early", "mid", "late"]


class Purchase(Model):
    item: Id
    cumulative_gold: Integer
    phase: Horizon
    purpose: Nonempty
    final_slot: Annotated[Integer, Field(ge=1, le=6)] | None = None
    quoted_cost: Integer | None = None
    quoted_consumption: list[Id] = Field(default_factory=list)

    @model_validator(mode="after")
    def quote(self):
        if self.quoted_consumption and self.quoted_cost is None:
            raise ValueError("Danh sách tiêu thụ giả định cần báo giá tại mốc mua.")
        return self


class PurchasePath(Model):
    id: Id
    steps: Annotated[list[Purchase], Field(min_length=1)]

    @model_validator(mode="after")
    def chronological(self):
        gold = [step.cumulative_gold for step in self.steps]
        slots = [step.final_slot for step in self.steps if step.final_slot is not None]
        if gold != sorted(gold) or slots != list(range(1, len(slots) + 1)):
            raise ValueError("Vàng tích lũy phải tăng dần và slot đích phải nối tiếp từ 1.")
        return self


class PurchaseScenario(Model):
    hero: Nonempty
    role: Nonempty
    paths: Annotated[list[PurchasePath], Field(min_length=1)]
    excluded_items: set[Id] = Field(default_factory=set)
    direct_component_credit: bool = False


def current_price(pack):
    price = pack["live"].get("stat.price", {}).get("value")
    if isinstance(price, dict) and price["unit"] == "gold":
        cost = price["amount"]
        if cost >= 0 and int(cost) == cost:
            return int(cost)
    return None


def purchase_step(step, pack, owned, packs, direct_credit):
    recipe = pack["live"].get("shop.recipe", {}).get("value")
    if step.quoted_cost is not None:
        consumed = Counter(step.quoted_consumption)
        if consumed - owned:
            raise ValueError(f"Báo giá {step.item} tiêu thụ thành phần chưa sở hữu.")
        if recipe is not None and consumed - Counter(key.split("/")[1] for key in recipe):
            raise ValueError(f"Báo giá {step.item} mâu thuẫn với công thức đã xác minh.")
        return step.quoted_cost, consumed, "scenario_quote"
    price = current_price(pack)
    if price is None:
        return None, Counter(), "unknown_price"
    if not owned:
        return price, Counter(), "live_full_price"
    if recipe is None:
        return None, Counter(), "unknown_recipe_with_inventory"
    consumed = Counter(key.split("/")[1] for key in recipe) & owned
    if not consumed:
        return price, consumed, "live_full_price"
    component_prices = {key: current_price(packs[key]) for key in consumed}
    if not direct_credit or None in component_prices.values():
        return None, consumed, "unknown_upgrade_cost"
    cost = price - sum(component_prices[key] * count for key, count in consumed.items())
    if cost < 0:
        return None, consumed, "inconsistent_upgrade_cost"
    return cost, consumed, "scenario_direct_component_credit"


def plan_purchases(repo: Repository, scenario: PurchaseScenario) -> dict:
    if scenario.role not in LANES:
        raise ValueError("Cần vị trí đấu hạng hợp lệ.")
    if len({path.id for path in scenario.paths}) != len(scenario.paths):
        raise ValueError("Mã lộ trình mua phải duy nhất.")
    player = repo.identify(scenario.hero)
    pref_path = repo.preferences.get(f"{player}/{scenario.role}")
    preference = repo.read_file(pref_path) if pref_path else None
    results = {}
    for path in scenario.paths:
        packs = {step.item: repo.get(f"items/{step.item}") for step in path.steps}
        disallowed = {
            key: choice
            for key, pack in packs.items()
            if (choice := eligibility(key, pack, preference))
            not in {"no_personal_filter", "reviewable"}
        }
        disallowed.update(
            {key: "excluded_by_scenario" for key in packs if key in scenario.excluded_items}
        )
        if disallowed:
            results[path.id] = {"status": "constraints_failed", "items": disallowed, "steps": []}
            continue
        owned, designated = Counter(), Counter()
        spent = 0
        rows = []
        for step in path.steps:
            row = step.model_dump(exclude={"quoted_cost", "quoted_consumption"})
            row.update(gold_before=step.cumulative_gold - spent, held_before=dict(owned))
            pack = packs[step.item]
            cost, consumed, basis = purchase_step(
                step, pack, owned, packs, scenario.direct_component_credit
            )
            row.update(cost=cost, cost_basis=basis, components_on_purchase=dict(consumed))
            rows.append(row)
            if cost is None:
                row["status"] = "unknown_cost"
                break
            if cost > row["gold_before"]:
                row.update(status="insufficient_gold", shortfall=cost - row["gold_before"])
                break
            if consumed - (owned - designated):
                row["status"] = "consumes_final_slot"
                break
            next_owned = owned - consumed + Counter({step.item: 1})
            if next_owned.total() > 6:
                row["status"] = "inventory_full"
                break
            owned = next_owned
            if step.final_slot is not None:
                designated[step.item] += 1
            spent += cost
            row.update(
                status="affordable_in_scenario",
                gold_after=step.cumulative_gold - spent,
                held_after=dict(owned),
                preference_checkpoint=step.final_slot in (preference or {}).get("checkpoints", []),
                added_live_stats={
                    prop: fact for prop, fact in pack["live"].items() if prop.startswith("stat.")
                },
                added_live_effects={
                    prop: fact
                    for prop, fact in pack["live"].items()
                    if isinstance(fact["value"], dict) and "effect" in fact["value"]
                },
            )
        complete = designated.total() == 6 and rows[-1]["status"] == "affordable_in_scenario"
        results[path.id] = {
            "status": "six_slots_affordable" if complete else "partial",
            "steps": rows,
            "spent": spent,
            "unreached_steps": len(path.steps) - len(rows),
        }
    return {
        "hero": player,
        "role": scenario.role,
        "paths": results,
        "scope": "Affordability and preference only. Quotes and component credit are scenario inputs; verify shop availability, stacking and item legality separately.",
    }


DamageKind = Literal["physical", "magic", "true"]


class Damage(Model):
    kind: DamageKind
    flat: Nonnegative = 0
    target_max_hp_ratio: Ratio = 0


class Heal(Model):
    amount: Nonnegative
    ready_at_s: Nonnegative | None
    condition_met: bool | None


class Shield(Model):
    amount: Nonnegative
    duration_s: Annotated[Nonnegative, Field(gt=0)]
    absorbs: set[DamageKind]


class Event(Model):
    at_s: Nonnegative
    damage: Damage | None = None
    heal: Heal | None = None
    shield: Shield | None = None

    @model_validator(mode="after")
    def one_effect(self):
        if sum(value is not None for value in (self.damage, self.heal, self.shield)) != 1:
            raise ValueError("Mỗi sự kiện cần đúng một hiệu ứng sát thương, hồi máu hoặc lá chắn.")
        return self


class HealWindow(Model):
    start_s: Nonnegative
    end_s: Nonnegative
    reduction: Ratio

    @model_validator(mode="after")
    def interval(self):
        if self.end_s <= self.start_s:
            raise ValueError("Cửa sổ giảm hồi phục cần thời lượng dương.")
        return self


class CooldownScenario(Model):
    base_s: Nonnegative
    started_at_s: Nonnegative
    cdr: Ratio
    cap: Ratio
    needed_at_s: Nonnegative


class Combat(Model):
    id: Id
    assumptions: Nonempty
    max_hp: Annotated[Nonnegative, Field(gt=0)]
    initial_hp: Annotated[Nonnegative, Field(gt=0)]
    physical_taken: Ratio | None = None
    magic_taken: Ratio | None = None
    anti_heal: list[HealWindow] = Field(default_factory=list)
    cooldown: CooldownScenario | None = None
    events: list[Event]

    @model_validator(mode="after")
    def sequence(self):
        times = [event.at_s for event in self.events]
        if self.initial_hp > self.max_hp or times != sorted(times):
            raise ValueError("HP ban đầu và thứ tự sự kiện không hợp lệ.")
        windows = sorted(self.anti_heal, key=lambda window: window.start_s)
        if any(
            left.end_s > right.start_s for left, right in zip(windows, windows[1:], strict=False)
        ):
            raise ValueError("Đầu vào chỉ nhận cửa sổ giảm hồi phục hiệu lực đã hợp nhất.")
        return self


class Comparison(Model):
    baseline: Combat
    alternatives: Annotated[list[Combat], Field(min_length=1)]


def evaluate_combat(case: Combat) -> dict:
    hp = case.initial_hp
    ledger = []
    cooldown = case.cooldown
    timing = None
    shield_remaining = shield_end = 0.0
    shield_types = set()
    if cooldown:
        ready = cooldown.started_at_s + cooldown.base_s * (1 - min(cooldown.cdr, cooldown.cap))
        if not isfinite(ready):
            raise ValueError("Thời điểm hồi chiêu vượt miền tính toán.")
        timing = {"ready_at_s": ready, "ready_by_needed_at_s": ready <= cooldown.needed_at_s}
    for event in case.events:
        row = {"at_s": event.at_s, "hp_before": hp}
        ledger.append(row)
        if event.at_s >= shield_end:
            shield_remaining = 0
        if event.damage:
            raw = event.damage.flat + case.max_hp * event.damage.target_max_hp_ratio
            if not isfinite(raw):
                raise ValueError("Sát thương vượt miền tính toán.")
            factor = {"physical": case.physical_taken, "magic": case.magic_taken, "true": 1}[
                event.damage.kind
            ]
            row.update(kind=event.damage.kind, raw=raw)
            if raw > 0 and factor is None:
                row["status"] = "unknown_damage_multiplier"
                hp = None
                break
            applied = raw * (factor or 0)
            absorbed = min(shield_remaining, applied) if event.damage.kind in shield_types else 0
            shield_remaining -= absorbed
            hp = max(0, hp - (applied - absorbed))
            row.update(damage_after_armor_layer=applied, absorbed=absorbed)
        elif event.heal:
            heal = event.heal
            if heal.condition_met is False or (
                heal.ready_at_s is not None and event.at_s < heal.ready_at_s
            ):
                row.update(kind="heal", effective_heal=0, status="unavailable")
            elif heal.condition_met is None or heal.ready_at_s is None:
                row.update(kind="heal", status="unknown_heal_availability")
                hp = None
                break
            else:
                reduction = next(
                    (w.reduction for w in case.anti_heal if w.start_s <= event.at_s < w.end_s), 0
                )
                effective = min(case.max_hp - hp, heal.amount * (1 - reduction))
                hp += effective
                row.update(kind="heal", effective_heal=effective, heal_reduction=reduction)
        else:
            row["kind"] = "shield"
            if shield_remaining > 0:
                row["status"] = "unknown_overlapping_shields"
                hp = None
                break
            shield_remaining = event.shield.amount
            shield_end = event.at_s + event.shield.duration_s
            if not isfinite(shield_end):
                raise ValueError("Thời điểm hết lá chắn vượt miền tính toán.")
            shield_types = event.shield.absorbs
        row["hp_after"] = hp
        row["shield_after"] = shield_remaining
        if hp == 0:
            break
    return {
        "assumptions": case.model_dump(exclude={"id", "events"}),
        "remaining_hp": hp,
        "depleted_at_s": ledger[-1]["at_s"] if hp == 0 else None,
        "cooldown_scenario": timing,
        "ledger": ledger,
    }


def compare_combat(comparison: Comparison) -> dict:
    cases = [comparison.baseline, *comparison.alternatives]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Mã tình huống what-if phải duy nhất.")
    results = {case.id: evaluate_combat(case) for case in cases}
    baseline_hp = results[comparison.baseline.id]["remaining_hp"]
    for result in results.values():
        hp = result["remaining_hp"]
        result["hp_delta_from_baseline"] = (
            hp - baseline_hp if None not in (hp, baseline_hp) else None
        )
    return {
        "baseline": comparison.baseline.id,
        "cases": results,
        "scope": "Scenario arithmetic over supplied events. Physical/magic factors include any assumed penetration. True damage skips this armor layer. Shield coverage comes from the scenario; overlapping shields, revives and unsupplied events have no modeled outcome.",
    }
