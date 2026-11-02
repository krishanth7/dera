"""Canonical, versioned static analysis contracts. Offsets are Unicode code points."""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Dialect = Literal["postgresql", "sqlite", "mysql", "mariadb"]
Safety = Literal["read_only_candidate", "unsafe", "unknown"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Span(Model):
    start: int
    end: int


class Diagnostic(Model):
    code: str
    message: str
    span: Span


class Statement(Model):
    statement_type: str
    objects: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    joins: list[str] = Field(default_factory=list)
    predicates: list[str] = Field(default_factory=list)
    parameters: list[str] = Field(default_factory=list)
    safety: Safety


class Analysis(Model):
    dialect: Dialect
    engine_version: str
    statement_count: int
    statements: list[Statement] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    unsupported_constructs: list[str] = Field(default_factory=list)
    safety: Safety

    def canonical_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
