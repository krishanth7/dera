"""DERA Reverse Engineering — Phase 6.1 Object Registry.

Provides an efficient, type-safe, duplicate-detecting object registry mapping
canonical ObjectIds to schema objects. Supports deterministic registration order,
kind-verified lookup, and explicit workspace scope preservation.

All operations are O(1) for lookup and registration. No silent replacement is
permitted — duplicate ObjectIds raise DuplicateRegistrationError immediately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from dera.metadata.enums import ObjectKind
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView
from dera.reverse_engineering.errors import (
    DuplicateRegistrationError,
    InvalidSchemaReferenceError,
)
from dera.reverse_engineering.references import TypedRef

if TYPE_CHECKING:
    pass

T = TypeVar("T")

# Type mapping: ObjectKind → expected Python type name for validation
_KIND_TO_TYPE: dict[str, type] = {
    ObjectKind.DATABASE: CanonicalDatabase,
    ObjectKind.NAMESPACE: CanonicalNamespace,
    ObjectKind.TABLE: CanonicalTable,
    ObjectKind.COLUMN: CanonicalColumn,
    ObjectKind.CONSTRAINT: CanonicalConstraint,
    ObjectKind.PRIMARY_KEY: CanonicalConstraint,
    ObjectKind.FOREIGN_KEY: CanonicalForeignKey,
    ObjectKind.UNIQUE_CONSTRAINT: CanonicalConstraint,
    ObjectKind.CHECK_CONSTRAINT: CanonicalConstraint,
    ObjectKind.INDEX: CanonicalIndex,
    ObjectKind.VIEW: CanonicalView,
    ObjectKind.TRIGGER: CanonicalTrigger,
}


def _parse_object_kind(object_id: str) -> str | None:
    """Extract the object kind token from a canonical ObjectId.

    ObjectId format: `dera:<object_kind>:<24_hex_chars>`
    Returns the object_kind string or None if the format is unrecognised.
    """
    parts = object_id.split(":", 2)
    if len(parts) == 3 and parts[0] == "dera":
        return parts[1]
    return None


class ObjectRegistry:
    """Efficient, type-safe registry mapping canonical ObjectIds to schema objects.

    Properties:
    - Deterministic registration order via insertion-ordered dict.
    - O(1) lookup by ObjectId.
    - Duplicate detection: DuplicateRegistrationError on conflict.
    - Kind-verified typed retrieval.
    - Workspace scope preserved from construction context.
    - No silent overwrite; no implicit upsert.
    """

    __slots__ = ("_objects", "_kind_index", "_workspace_id")

    def __init__(self, workspace_id: str | None = None) -> None:
        """Initialise an empty registry.

        Args:
            workspace_id: Optional workspace scope for multi-tenant isolation.
        """
        self._objects: dict[str, Any] = {}
        self._kind_index: dict[str, list[str]] = {k.value: [] for k in ObjectKind}
        self._workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, object_id: str, obj: Any, kind: str) -> None:
        """Register a schema object under its canonical ObjectId.

        Args:
            object_id: Canonical ObjectId in `dera:<kind>:<hex>` format.
            obj: The schema object instance.
            kind: ObjectKind string for validation and kind index.

        Raises:
            DuplicateRegistrationError: If object_id is already registered.
        """
        if object_id in self._objects:
            raise DuplicateRegistrationError(object_id, kind)
        self._objects[object_id] = obj
        kind_key = kind.lower()
        if kind_key not in self._kind_index:
            self._kind_index[kind_key] = []
        self._kind_index[kind_key].append(object_id)

    def register_database(self, db: CanonicalDatabase) -> None:
        """Register a CanonicalDatabase."""
        self.register(db.id, db, ObjectKind.DATABASE)

    def register_namespace(self, ns: CanonicalNamespace) -> None:
        """Register a CanonicalNamespace."""
        self.register(ns.id, ns, ObjectKind.NAMESPACE)

    def register_table(self, table: CanonicalTable) -> None:
        """Register a CanonicalTable."""
        self.register(table.id, table, ObjectKind.TABLE)

    def register_column(self, col: CanonicalColumn) -> None:
        """Register a CanonicalColumn."""
        self.register(col.id, col, ObjectKind.COLUMN)

    def register_constraint(self, constraint: CanonicalConstraint) -> None:
        """Register a CanonicalConstraint."""
        self.register(constraint.id, constraint, ObjectKind.CONSTRAINT)

    def register_foreign_key(self, fk: CanonicalForeignKey) -> None:
        """Register a CanonicalForeignKey."""
        self.register(fk.id, fk, ObjectKind.FOREIGN_KEY)

    def register_index(self, index: CanonicalIndex) -> None:
        """Register a CanonicalIndex."""
        self.register(index.id, index, ObjectKind.INDEX)

    def register_view(self, view: CanonicalView) -> None:
        """Register a CanonicalView."""
        self.register(view.id, view, ObjectKind.VIEW)

    def register_trigger(self, trigger: CanonicalTrigger) -> None:
        """Register a CanonicalTrigger."""
        self.register(trigger.id, trigger, ObjectKind.TRIGGER)

    # ------------------------------------------------------------------
    # Generic lookup
    # ------------------------------------------------------------------

    def get_object(self, object_id: str) -> Any | None:
        """Return any registered object by ObjectId, or None if not found."""
        return self._objects.get(object_id)

    def contains(self, object_id: str) -> bool:
        """Return True if the ObjectId is registered."""
        return object_id in self._objects

    # ------------------------------------------------------------------
    # Type-safe typed lookup
    # ------------------------------------------------------------------

    def _get_typed(self, object_id: str, expected_kind: str, expected_type: type) -> Any:
        """Internal type-safe retrieval with kind verification.

        Raises:
            InvalidSchemaReferenceError: If object not found or wrong kind.
        """
        obj = self._objects.get(object_id)
        if obj is None:
            raise InvalidSchemaReferenceError(object_id, expected_kind)
        if not isinstance(obj, expected_type):
            actual_kind = _parse_object_kind(object_id) or type(obj).__name__
            raise InvalidSchemaReferenceError(object_id, expected_kind, actual_kind)
        return obj

    def get_database(self, object_id: str) -> CanonicalDatabase:
        """Return a CanonicalDatabase by ObjectId.

        Raises:
            InvalidSchemaReferenceError: If not found or wrong kind.
        """
        return self._get_typed(object_id, ObjectKind.DATABASE, CanonicalDatabase)

    def get_namespace(self, object_id: str) -> CanonicalNamespace:
        """Return a CanonicalNamespace by ObjectId."""
        return self._get_typed(object_id, ObjectKind.NAMESPACE, CanonicalNamespace)

    def get_table(self, object_id: str) -> CanonicalTable:
        """Return a CanonicalTable by ObjectId."""
        return self._get_typed(object_id, ObjectKind.TABLE, CanonicalTable)

    def get_column(self, object_id: str) -> CanonicalColumn:
        """Return a CanonicalColumn by ObjectId."""
        return self._get_typed(object_id, ObjectKind.COLUMN, CanonicalColumn)

    def get_constraint(self, object_id: str) -> CanonicalConstraint:
        """Return a CanonicalConstraint by ObjectId."""
        return self._get_typed(object_id, ObjectKind.CONSTRAINT, CanonicalConstraint)

    def get_foreign_key(self, object_id: str) -> CanonicalForeignKey:
        """Return a CanonicalForeignKey by ObjectId."""
        return self._get_typed(object_id, ObjectKind.FOREIGN_KEY, CanonicalForeignKey)

    def get_index(self, object_id: str) -> CanonicalIndex:
        """Return a CanonicalIndex by ObjectId."""
        return self._get_typed(object_id, ObjectKind.INDEX, CanonicalIndex)

    def get_view(self, object_id: str) -> CanonicalView:
        """Return a CanonicalView by ObjectId."""
        return self._get_typed(object_id, ObjectKind.VIEW, CanonicalView)

    def get_trigger(self, object_id: str) -> CanonicalTrigger:
        """Return a CanonicalTrigger by ObjectId."""
        return self._get_typed(object_id, ObjectKind.TRIGGER, CanonicalTrigger)

    # ------------------------------------------------------------------
    # Reference resolution
    # ------------------------------------------------------------------

    def resolve_ref(self, ref: TypedRef) -> TypedRef:
        """Resolve a TypedRef against the registry.

        Returns an updated TypedRef with the appropriate ResolutionStatus:
        - RESOLVED if the target is found with the expected kind.
        - INVALID if the ObjectId format is unrecognised.
        - MISSING if the target is not in the registry.
        - MISSING with note if found but wrong kind (kind mismatch reported).
        """
        if not ref.target_id or not ref.target_id.startswith("dera:"):
            return ref.mark_invalid()

        obj = self._objects.get(ref.target_id)
        if obj is None:
            return ref.mark_missing()

        # Verify kind via ObjectId prefix parsing
        actual_kind = _parse_object_kind(ref.target_id)
        if actual_kind and actual_kind != ref.expected_kind:
            # Kind mismatch — return INVALID to signal caller
            return ref.mark_invalid()

        return ref.resolve()

    # ------------------------------------------------------------------
    # Kind-indexed collection access
    # ------------------------------------------------------------------

    def all_of_kind(self, kind: str) -> tuple[Any, ...]:
        """Return all registered objects of a specific ObjectKind."""
        ids = self._kind_index.get(kind.lower(), [])
        return tuple(self._objects[oid] for oid in ids if oid in self._objects)

    def all_tables(self) -> tuple[CanonicalTable, ...]:
        """Return all registered CanonicalTable objects."""
        return tuple(
            obj for obj in self.all_of_kind(ObjectKind.TABLE) if isinstance(obj, CanonicalTable)
        )

    def all_namespaces(self) -> tuple[CanonicalNamespace, ...]:
        """Return all registered CanonicalNamespace objects."""
        return tuple(
            obj
            for obj in self.all_of_kind(ObjectKind.NAMESPACE)
            if isinstance(obj, CanonicalNamespace)
        )

    def all_columns(self) -> tuple[CanonicalColumn, ...]:
        """Return all registered CanonicalColumn objects."""
        return tuple(
            obj for obj in self.all_of_kind(ObjectKind.COLUMN) if isinstance(obj, CanonicalColumn)
        )

    def all_foreign_keys(self) -> tuple[CanonicalForeignKey, ...]:
        """Return all registered CanonicalForeignKey objects."""
        return tuple(
            obj
            for obj in self.all_of_kind(ObjectKind.FOREIGN_KEY)
            if isinstance(obj, CanonicalForeignKey)
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @property
    def total_objects(self) -> int:
        """Total count of registered schema objects."""
        return len(self._objects)

    @property
    def workspace_id(self) -> str | None:
        """Workspace scope for this registry, or None if unscoped."""
        return self._workspace_id

    def object_count_by_kind(self) -> dict[str, int]:
        """Return a mapping of object kind → count."""
        return {kind: len(ids) for kind, ids in self._kind_index.items() if ids}

    def __len__(self) -> int:
        return self.total_objects

    def __repr__(self) -> str:
        counts = self.object_count_by_kind()
        return f"ObjectRegistry(total={self.total_objects}, workspace={self._workspace_id!r}, kinds={counts})"
