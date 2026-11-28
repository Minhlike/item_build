from datetime import date
from enum import StrEnum
from math import isfinite
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, HttpUrl, model_validator

Id = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
Property = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")]
Nonempty = Annotated[str, Field(min_length=1)]
Nonnegative = Annotated[FiniteFloat, Field(ge=0)]
Integer = Annotated[int, Field(strict=True, ge=0)]
Kind = Literal["heroes", "items", "runes", "enchantments", "spells", "battlefield", "roles"]
RelationType = Literal[
    "HAS_ABILITY",
    "TRIGGERS",
    "REQUIRES",
    "SCALES_WITH",
    "DEALS_DAMAGE",
    "APPLIES_EFFECT",
    "COUNTERS",
    "MITIGATES",
    "AMPLIFIES",
    "SYNERGIZES_WITH",
    "CONFLICTS_WITH",
    "RESETS_COOLDOWN",
    "REDUCES_COOLDOWN",
    "STACKS_WITH",
    "DOES_NOT_STACK_WITH",
    "THREATENS",
    "ENABLES_TACTIC",
    "DEPENDS_ON",
    "SUPERSEDES",
]
ClaimType = Literal[
    "mechanical_fact",
    "derived_knowledge",
    "behavioral_tendency",
    "tactical_heuristic",
    "unverified_hypothesis",
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Status(StrEnum):
    LIVE_VN = "LIVE_VN"
    UPCOMING_VN = "UPCOMING_VN"
    EXPERIMENTAL = "EXPERIMENTAL"
    OTHER_REGION = "OTHER_REGION"
    UNVERIFIED = "UNVERIFIED"
    SUPERSEDED = "SUPERSEDED"


class Evidence(Model):
    source_id: Nonempty
    source_url: HttpUrl
    source_type: Literal["official", "official_academy", "user_experiment", "community_repository"]
    server: Nonempty
    published_at: date | None = None
    retrieved_at: date
    effective_from: date | None = None
    effective_until: date | None = None
    patch_id: Id | None = None
    verification_status: Literal[
        "verified_official", "cross_checked", "experiment", "unverified", "conflict"
    ]
    evidence_ref: Nonempty

    @model_validator(mode="after")
    def valid_interval(self):
        if self.effective_until and (
            not self.effective_from or self.effective_until <= self.effective_from
        ):
            raise ValueError("Khoảng hiệu lực nguồn không hợp lệ.")
        if self.published_at and self.retrieved_at < self.published_at:
            raise ValueError("Ngày truy xuất trước ngày công bố.")
        return self


class Unit(StrEnum):
    DAMAGE = "damage"
    HP = "hp"
    SECOND = "second"
    RATIO = "ratio"
    COUNT = "count"
    GOLD = "gold"
    EXPERIENCE = "experience"
    METER = "meter"
    MANA = "mana"
    ARMOR = "armor"
    MAGIC_DEFENSE = "magic_defense"
    ATTACK_DAMAGE = "attack_damage"
    ABILITY_POWER = "ability_power"
    MOVE_SPEED = "move_speed"
    HP_PER_5_SECONDS = "hp_per_5_seconds"


class Quantity(Model):
    amount: FiniteFloat
    unit: Unit


class Basis(StrEnum):
    CASTER_MAX_HP = "caster_max_hp"
    CASTER_CURRENT_HP = "caster_current_hp"
    CASTER_MISSING_HP = "caster_missing_hp"
    CASTER_BONUS_HP = "caster_bonus_hp"
    TARGET_MAX_HP = "target_max_hp"
    TARGET_CURRENT_HP = "target_current_hp"
    TARGET_MISSING_HP = "target_missing_hp"
    BASE_AD = "base_ad"
    BONUS_AD = "bonus_ad"
    TOTAL_AD = "total_ad"
    UNSPECIFIED_AD = "unspecified_ad"
    AP = "ap"
    BONUS_AP = "bonus_ap"
    HERO_LEVEL = "hero_level"
    SKILL_RANK = "skill_rank"
    DAMAGE_DEALT = "damage_dealt"
    INCOMING_PRE_MITIGATION_DAMAGE = "incoming_pre_mitigation_damage"


CONVERSION = {
    **{basis: {Unit.HP, Unit.DAMAGE} for basis in Basis if basis.value.endswith("_hp")},
    **{
        basis: {Unit.DAMAGE, Unit.HP}
        for basis in (
            Basis.BASE_AD,
            Basis.BONUS_AD,
            Basis.TOTAL_AD,
            Basis.UNSPECIFIED_AD,
            Basis.AP,
            Basis.BONUS_AP,
            Basis.DAMAGE_DEALT,
            Basis.INCOMING_PRE_MITIGATION_DAMAGE,
        )
    },
    Basis.HERO_LEVEL: set(Unit),
    Basis.SKILL_RANK: set(Unit),
}


class Term(Model):
    basis: Basis
    coefficient: FiniteFloat
    origin: Integer | None = None
    multiply_by_target_max_hp: bool = False

    @model_validator(mode="after")
    def origin_only_for_levels(self):
        if self.origin is not None and self.basis not in {Basis.HERO_LEVEL, Basis.SKILL_RANK}:
            raise ValueError("Mốc cấp chỉ áp dụng với cấp tướng hoặc chiêu.")
        return self


class Formula(Model):
    unit: Unit
    base: Nonnegative
    terms: list[Term] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_units(self):
        if any(self.unit not in CONVERSION[term.basis] for term in self.terms):
            raise ValueError("Đơn vị kết quả không tương thích với cơ sở tính.")
        if len({term.basis for term in self.terms}) != len(self.terms):
            raise ValueError("Cơ sở công thức bị lặp.")
        for term in self.terms:
            if term.multiply_by_target_max_hp and (
                self.unit != Unit.DAMAGE
                or term.basis
                not in {
                    Basis.BASE_AD,
                    Basis.BONUS_AD,
                    Basis.TOTAL_AD,
                    Basis.UNSPECIFIED_AD,
                    Basis.AP,
                }
            ):
                raise ValueError(
                    "Hệ số theo máu tối đa mục tiêu cần cơ sở công và đơn vị sát thương."
                )
        return self

    def calculate(self, inputs: dict[Basis, Nonnegative]) -> float:
        result = self.base
        for term in self.terms:
            if term.basis not in inputs:
                raise ValueError(f"Thiếu giá trị {term.basis}.")
            value = float(inputs[term.basis])
            if not isfinite(value) or value < 0:
                raise ValueError(f"Giá trị {term.basis} không hợp lệ.")
            if term.basis in {Basis.HERO_LEVEL, Basis.SKILL_RANK}:
                if term.origin is None or not value.is_integer() or value < max(1, term.origin):
                    raise ValueError("Cần cấp nguyên và mốc cấp đã xác minh.")
                value -= term.origin
            if term.multiply_by_target_max_hp:
                target_hp = inputs.get(Basis.TARGET_MAX_HP)
                if target_hp is None or not isfinite(target_hp) or target_hp <= 0:
                    raise ValueError("Cần máu tối đa mục tiêu dương.")
                value *= target_hp
            result += value * term.coefficient
        if not isfinite(result) or result < 0:
            raise ValueError("Kết quả công thức ngoài miền giá trị.")
        return result


class Effect(StrEnum):
    DAMAGE = "damage"
    HEAL = "heal"
    LIFESTEAL = "lifesteal"
    SPELL_LIFESTEAL = "spell_lifesteal"
    HEAL_REDUCTION = "heal_reduction"
    SHIELD = "shield"
    DAMAGE_REDUCTION = "damage_reduction"
    DAMAGE_IMMUNITY = "damage_immunity"
    TENACITY = "tenacity"
    CC_IMMUNITY = "cc_immunity"
    CLEANSE = "cleanse"
    UNTARGETABLE = "untargetable"
    STEALTH = "stealth"
    CAMOUFLAGE = "camouflage"
    REVEAL = "reveal"
    HARD_CC = "hard_cc"
    SOFT_CC = "soft_cc"
    DASH = "dash"
    TELEPORT = "teleport"
    ACCRUE_STACK = "accrue_stack"
    SPEND_STACK = "spend_stack"
    EMPOWERED_ATTACK = "empowered_attack"
    ON_HIT = "on_hit"
    RESET_COOLDOWN = "reset_cooldown"
    REDUCE_COOLDOWN = "reduce_cooldown"
    CHARGE = "charge"
    TRANSFORM = "transform"
    REVIVE = "revive"
    TURRET = "turret"
    JUNGLE = "jungle"
    ECONOMY = "economy"
    RESOURCE = "resource"
    STAT_CHANGE = "stat_change"
    ATTACK_SPEED = "attack_speed"
    ARMOR_PEN = "armor_pen"
    MAGIC_PEN = "magic_pen"
    ARMOR_REDUCTION = "armor_reduction"
    CRITICAL = "critical"
    UNIQUE_PASSIVE = "unique_passive"
    SPECIAL = "special"


class Timing(Model):
    duration_s: Nonnegative | None = None
    interval_s: Nonnegative | None = None
    cooldown_s: Nonnegative | Formula | list[Nonnegative] | None = None
    cooldown_start: Literal["cast", "end", "hit"] | None = None
    cast_s: Nonnegative | None = None
    internal_cooldown_s: Nonnegative | None = None
    recharge_s: Nonnegative | None = None

    @model_validator(mode="after")
    def cooldown_unit(self):
        if isinstance(self.cooldown_s, Formula) and self.cooldown_s.unit != Unit.SECOND:
            raise ValueError("Hồi chiêu phải có đơn vị giây.")
        if self.cooldown_s == []:
            raise ValueError("Bảng hồi chiêu trống.")
        return self


class Mechanic(Model):
    effect: Effect
    actor: Nonempty = "caster"
    target: Nonempty
    delivery: (
        Literal[
            "basic_attack", "empowered_attack", "ability", "passive", "item", "spell", "battlefield"
        ]
        | None
    ) = None
    trigger: Nonempty
    activation: Literal["manual", "automatic"] | None = None
    detail: Nonempty | None = None
    damage_type: Literal["physical", "magic", "true"] | None = None
    basis: Basis | None = None
    amount: Quantity | None = None
    formula: Formula | None = None
    timing: Timing | None = None
    stacks: Integer | None = None
    charges: Integer | None = None
    hero_level: Integer | None = None
    skill_rank: Integer | None = None
    radius: Nonnegative | None = None
    ends_when: Nonempty | None = None
    exceptions: list[Nonempty] = Field(default_factory=list)
    interactions: list[Nonempty] = Field(default_factory=list)
    unique_group: Id | None = None

    @model_validator(mode="after")
    def effect_matches_type(self):
        if (self.effect == Effect.DAMAGE) != (self.damage_type is not None):
            raise ValueError("Thành phần sát thương phải có đúng một loại sát thương.")
        allowed = {Effect.DAMAGE: {Unit.DAMAGE}, Effect.HEAL: {Unit.HP}, Effect.SHIELD: {Unit.HP}}
        for quantity in (self.formula, self.amount):
            if quantity and self.effect in allowed and quantity.unit not in allowed[self.effect]:
                raise ValueError("Đơn vị số liệu không hợp lệ với hiệu ứng.")
        if self.formula and self.amount:
            raise ValueError("Chọn công thức hoặc số đo cho một thành phần.")
        return self


class Claim(Model):
    evidence: list[Id] = Field(min_length=1)
    status: Status = Status.UNVERIFIED
    kind: ClaimType = "mechanical_fact"
    effective_from: date | None = None
    effective_until: date | None = None

    @model_validator(mode="after")
    def effective_dates(self):
        if (
            self.effective_until
            and self.effective_from
            and self.effective_until <= self.effective_from
        ):
            raise ValueError("Khoảng hiệu lực thuộc tính không hợp lệ.")
        if self.status in {Status.LIVE_VN, Status.UPCOMING_VN} and not self.effective_from:
            raise ValueError("Thuộc tính có phiên bản phải có ngày hiệu lực.")
        if self.status == Status.SUPERSEDED and not self.effective_until:
            raise ValueError("Thuộc tính bị thay thế phải có ngày kết thúc.")
        if self.status == Status.LIVE_VN and self.kind == "unverified_hypothesis":
            raise ValueError("Giả thuyết không được phát hành LIVE_VN.")
        return self

    def live_at(self, day: date) -> bool:
        return (
            self.status == Status.LIVE_VN
            and self.effective_from <= day
            and (self.effective_until is None or day < self.effective_until)
        )


class Fact(Claim):
    value: Mechanic | Quantity | Nonempty | bool | list[Nonempty]


class Entity(Model):
    id: Id
    kind: Kind
    name: Nonempty
    aliases: list[Nonempty] = Field(default_factory=list)
    facts: dict[Property, list[Fact]] = Field(default_factory=dict)
    unknown: list[Nonempty] = Field(default_factory=list)
    shop_group: Literal["defense", "physical", "magic", "support", "boots", "jungle"] | None = None

    @model_validator(mode="after")
    def item_group(self):
        if (self.kind == "items") != (self.shop_group is not None):
            raise ValueError("Mỗi trang bị cần một nhóm cửa hàng.")
        return self


class Relation(Claim):
    id: Id
    subject: Nonempty
    predicate: RelationType
    object: Nonempty
    condition: Nonempty
    scope: Nonempty


class CanonicalEntity(Entity):
    relations: list[Relation]


class Change(Model):
    entity: Nonempty
    property: Property
    classification: Literal["buff", "nerf", "rework", "bug_fix", "correction", "addition"]
    replacement: Fact
    previous: Fact | None = None


class Patch(Model):
    id: Id
    title: Nonempty
    status: Status
    server: Nonempty
    effective_from: date
    evidence: Id
    changes: list[Change] = Field(default_factory=list)
    review_notes: list[Nonempty] = Field(default_factory=list)


class Release(Model):
    patch_id: Id
    as_of: date
    readiness: Literal["PARTIAL_READY", "READY_FOR_USE"]
    gaps: list[Nonempty]

    @model_validator(mode="after")
    def known_gaps(self):
        if self.readiness == "READY_FOR_USE" and self.gaps:
            raise ValueError("Release còn khoảng trống.")
        return self
