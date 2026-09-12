#!/usr/bin/env python3
"""Rebuild one ORD physical-to-logical-to-target chain from public Git LFS.

The command deliberately has no ``--source-root`` option.  It gets immutable
ORD Parquet objects through the public Git LFS batch protocol, verifies each
object against the frozen source manifest, and writes every derivative under
an explicitly supplied empty output root.  A caller must keep ``--download-root``
outside the repository: original Parquet is a transient public input, never a
release artifact.

The Ahneman percent-yield standardized projection contract is presently
extracted. Unsupported targets fail closed rather than silently applying a
different label or feature policy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq
from google.protobuf.json_format import MessageToDict, ParseDict
from jsonschema import Draft202012Validator
from ord_schema import UnitMessage, units
from ord_schema.proto import reaction_pb2
from rdkit import Chem

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from build_corpus_staging import CORPUS_HEADER, build as build_corpus

VERSION = "1.0.0"
LFS_POINTER_VERSION = "https://git-lfs.github.com/spec/v1"
LFS_ACCEPT = "application/vnd.git-lfs+json"
PARQUET_BATCH_SIZE = 1024


# These are frozen, source-independent projection contracts.  They were
# extracted from the original standardized target builder and intentionally do
# not read the original target package at runtime.  A target without an entry
# here fails closed: it is unsafe to substitute a lossy generic two-column
# label table for a model-ready standardized target.
TARGET_CONTRACTS: dict[str, dict[str, object]] = {
    "ahneman_yield_percent": {
        "adapter_version": "wave-a-labels-v1",
        "columns": (
            "reactant-1",
            "reactant-2",
            "reagent-1",
            "reagent-2",
            "catalyst-1",
            "solvent-1",
            "solvent-2",
            "solvent-3",
            "solvent-4",
            "solvent-5",
            "product",
            "temperature_c",
            "reaction_time_s",
            "yield_percent",
        ),
        "column_roles": {
            "reactants": ("reactant-1", "reactant-2"),
            "others": (
                "reagent-1",
                "reagent-2",
                "catalyst-1",
                "solvent-1",
                "solvent-2",
                "solvent-3",
                "solvent-4",
                "solvent-5",
            ),
            "products": ("product",),
            "conditions": ("temperature_c", "reaction_time_s"),
        },
        "role_limits": {"reactant": 2, "reagent": 2, "catalyst": 1, "solvent": 5},
        "numeric_conditions": ("temperature_c", "reaction_time_s"),
        "project_name": "ahneman_yield_structure_v1",
        "requires_product": True,
    }
}
ROLE_ENUM_TO_NAME = {
    reaction_pb2.ReactionRole.REACTANT: "reactant",
    reaction_pb2.ReactionRole.REAGENT: "reagent",
    reaction_pb2.ReactionRole.CATALYST: "catalyst",
    reaction_pb2.ReactionRole.SOLVENT: "solvent",
}
IDENTIFIER_PRIORITY = ("SMILES", "CXSMILES", "INCHI", "MOLBLOCK")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial")
    if temporary.exists():
        raise FileExistsError(f"refusing to replace existing temporary file: {temporary}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def nonempty_clean_directory(path: Path, label: str) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"{label} must be empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def parse_json_array(row: dict[str, str], field: str) -> list[str]:
    value = json.loads(row[field])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a JSON string array")
    return value


def raw_lfs_pointer_url(source: dict[str, str]) -> str:
    repo = urllib.parse.urlparse(source["upstream_repo_url"])
    if repo.scheme != "https" or repo.netloc != "github.com" or not repo.path.endswith(".git"):
        raise ValueError("source manifest upstream_repo_url must be an HTTPS github.com Git repository")
    repository = repo.path.strip("/")[:-4]
    if repository.count("/") != 1:
        raise ValueError("source manifest upstream repository path is invalid")
    return f"https://raw.githubusercontent.com/{repository}/{source['upstream_revision']}/{source['upstream_path']}"


def lfs_batch_endpoint(source: dict[str, str]) -> str:
    repository_url = source["upstream_repo_url"].removesuffix("/")
    if not repository_url.endswith(".git"):
        raise ValueError("source manifest upstream_repo_url must end in .git")
    return f"{repository_url}/info/lfs/objects/batch"


def fetch_bytes(request: urllib.request.Request, timeout_seconds: int) -> bytes:
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - hosts are validated below.
        return response.read()


def parse_lfs_pointer(payload: bytes) -> tuple[str, int]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("pinned raw URL did not return a UTF-8 Git LFS pointer") from error
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition(" ")
        if separator:
            fields[key] = value.strip()
    if fields.get("version") != LFS_POINTER_VERSION:
        raise ValueError("pinned raw URL did not return a Git LFS pointer")
    oid = fields.get("oid", "")
    if not oid.startswith("sha256:") or len(oid.removeprefix("sha256:")) != 64:
        raise ValueError("Git LFS pointer has no SHA-256 oid")
    try:
        size = int(fields["size"])
    except (KeyError, ValueError) as error:
        raise ValueError("Git LFS pointer has no valid size") from error
    if size < 1:
        raise ValueError("Git LFS pointer size must be positive")
    return oid.removeprefix("sha256:"), size


def lfs_download_action(source: dict[str, str], oid: str, size: int, timeout_seconds: int) -> tuple[str, dict[str, str]]:
    request_body = canonical_json({"operation": "download", "transfers": ["basic"], "objects": [{"oid": oid, "size": size}]}).encode("utf-8")
    request = urllib.request.Request(
        lfs_batch_endpoint(source),
        data=request_body,
        method="POST",
        headers={"Accept": LFS_ACCEPT, "Content-Type": LFS_ACCEPT},
    )
    try:
        response = json.loads(fetch_bytes(request, timeout_seconds).decode("utf-8"))
        objects = response["objects"]
        object_record = objects[0]
        action = object_record["actions"]["download"]
        href = action["href"]
    except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("public Git LFS batch response has no usable download action") from error
    if len(objects) != 1 or object_record.get("oid") != oid or int(object_record.get("size", -1)) != size:
        raise ValueError("public Git LFS batch response does not match the requested object")
    parsed = urllib.parse.urlparse(href)
    allowed_hosts = {"github.com", "github-cloud.githubusercontent.com"}
    if parsed.scheme != "https" or parsed.netloc not in allowed_hosts or parsed.username or parsed.password:
        raise ValueError("public Git LFS download action has an unexpected host")
    headers = action.get("header", {})
    if not isinstance(headers, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in headers.items()):
        raise ValueError("public Git LFS download action has invalid headers")
    return href, headers


def download_lfs_source(source: dict[str, str], download_root: Path, timeout_seconds: int) -> dict[str, object]:
    """Download one public LFS object and return non-secret verification evidence."""
    raw_url = raw_lfs_pointer_url(source)
    pointer_request = urllib.request.Request(raw_url, headers={"Accept": "text/plain"})
    pointer_oid, pointer_size = parse_lfs_pointer(fetch_bytes(pointer_request, timeout_seconds))
    expected_oid = source["git_lfs_oid"]
    expected_size = int(source["size_bytes"])
    if pointer_oid != expected_oid or pointer_oid != source["source_sha256"] or pointer_size != expected_size:
        raise ValueError(f"pinned LFS pointer disagrees with frozen source manifest: {source['physical_dataset_id']}")
    href, headers = lfs_download_action(source, pointer_oid, pointer_size, timeout_seconds)
    destination = download_root / f"{source['physical_dataset_id']}.parquet"
    temporary = destination.with_name(f".{destination.name}.partial")
    if destination.exists() or temporary.exists():
        raise FileExistsError(f"refusing to overwrite downloaded source: {destination}")
    request = urllib.request.Request(href, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response, temporary.open("wb") as handle:  # noqa: S310 - action host is validated above.
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    actual_hash = sha256(temporary)
    actual_size = temporary.stat().st_size
    if actual_hash != expected_oid or actual_size != expected_size:
        temporary.unlink()
        raise ValueError(f"downloaded LFS object hash or size disagrees with source manifest: {source['physical_dataset_id']}")
    os.replace(temporary, destination)
    return {
        "physical_dataset_id": source["physical_dataset_id"],
        "raw_lfs_pointer_url": raw_url,
        "lfs_batch_endpoint": lfs_batch_endpoint(source),
        "lfs_batch_protocol": "basic",
        "ephemeral_download_action_url_persisted": False,
        "source_sha256": actual_hash,
        "size_bytes": actual_size,
        "path": destination,
    }


def parquet_to_physical_csv(parquet_path: Path, source: dict[str, str], output_path: Path) -> dict[str, object]:
    """Stream a verified ORD Parquet object into the legacy-compatible physical CSV."""
    if sha256(parquet_path) != source["source_sha256"]:
        raise ValueError(f"Parquet hash changed before conversion: {source['physical_dataset_id']}")
    parquet = pq.ParquetFile(parquet_path)
    names = set(parquet.schema_arrow.names)
    if names != {"reaction_id", "reaction"}:
        raise ValueError(f"ORD Parquet has unexpected columns: {sorted(names)}")
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        # The legacy physical layer has exactly these two columns and CRLF
        # records.  Logical assembly adds immutable source lineage later.
        writer = csv.DictWriter(handle, fieldnames=["reaction_id", "reaction_json"], lineterminator="\r\n")
        writer.writeheader()
        for batch in parquet.iter_batches(batch_size=PARQUET_BATCH_SIZE, columns=["reaction_id", "reaction"]):
            reaction_ids = batch.column(0).to_pylist()
            reactions = batch.column(1).to_pylist()
            for reaction_id, serialized in zip(reaction_ids, reactions, strict=True):
                if not isinstance(reaction_id, str) or not isinstance(serialized, bytes):
                    raise ValueError("ORD Parquet reaction_id/reaction types are invalid")
                reaction = reaction_pb2.Reaction()
                reaction.ParseFromString(serialized)
                if reaction.reaction_id != reaction_id:
                    raise ValueError("ORD Parquet reaction column disagrees with its reaction_id column")
                writer.writerow(
                    {
                        "reaction_id": reaction_id,
                        "reaction_json": json.dumps(
                            MessageToDict(reaction, preserving_proto_field_name=True), ensure_ascii=False, separators=(",", ":")
                        ),
                    }
                )
                count += 1
    if count != int(source["reaction_count"]):
        raise ValueError(f"Parquet row count disagrees with source manifest: {source['physical_dataset_id']}")
    return {"physical_dataset_id": source["physical_dataset_id"], "row_count": count, "sha256": sha256(output_path), "size_bytes": output_path.stat().st_size}


def assemble_logical_csv(physical_csvs: list[tuple[dict[str, str], Path]], output_path: Path) -> dict[str, object]:
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CORPUS_HEADER, lineterminator="\n")
        writer.writeheader()
        for source, physical_csv in sorted(physical_csvs, key=lambda item: item[0]["upstream_path"]):
            with physical_csv.open(encoding="utf-8", newline="") as input_handle:
                reader = csv.DictReader(input_handle)
                if reader.fieldnames != ["reaction_id", "reaction_json"]:
                    raise ValueError(f"physical CSV has an unexpected header: {physical_csv}")
                for expected_index, row in enumerate(reader):
                    writer.writerow(
                        {
                            "physical_dataset_id": source["physical_dataset_id"],
                            "source_file": source["upstream_path"],
                            "reaction_id": row["reaction_id"],
                            "row_index": expected_index,
                            "reaction_json": row["reaction_json"],
                        }
                    )
                    count += 1
    return {"row_count": count, "sha256": sha256(output_path), "size_bytes": output_path.stat().st_size}


def decision_id(target_id: str, physical_id: str, row_index: str, reaction_id: str, decision: str) -> str:
    material = "\0".join((target_id, physical_id, row_index, reaction_id, decision)).encode("utf-8")
    return f"label-{hashlib.sha256(material).hexdigest()[:24]}"


def enum_name(message: Any, field_name: str) -> str:
    """Return an ORD enum name without depending on JSON enum conversion."""
    descriptor = message.DESCRIPTOR
    field = descriptor.fields_by_name[field_name]
    if field.enum_type is None:
        raise TypeError(f"field is not an enum: {field_name}")
    return field.enum_type.values_by_number[int(getattr(message, field_name))].name


def optional_scalar(message: Any, field_name: str) -> tuple[bool, object | None]:
    """Keep protobuf scalar presence distinct from a present zero."""
    if not message.HasField(field_name):
        return False, None
    return True, getattr(message, field_name)


def canonical_smiles(identifiers: Iterable[Any]) -> tuple[str, str]:
    """Mirror the frozen SMILES>CXSMILES>InChI>MOLBLOCK projection policy."""
    by_type: dict[str, list[Any]] = {}
    for identifier in identifiers:
        by_type.setdefault(enum_name(identifier, "type"), []).append(identifier)
    for identifier_type in IDENTIFIER_PRIORITY:
        for identifier in by_type.get(identifier_type, []):
            raw_value = identifier.value.strip()
            if not raw_value:
                continue
            try:
                if identifier_type in {"SMILES", "CXSMILES"}:
                    molecule = Chem.MolFromSmiles(raw_value)
                elif identifier_type == "INCHI":
                    molecule = Chem.MolFromInchi(raw_value)
                else:
                    molecule = Chem.MolFromMolBlock(raw_value, sanitize=True)
                if molecule is None:
                    continue
                result = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
            except (RuntimeError, ValueError):
                continue
            if result:
                return result, "ok"
    return "", "missing_or_unparseable_identifier"


def collect_components(reaction: reaction_pb2.Reaction) -> dict[str, list[str]]:
    """Collect source components in the frozen target-builder slot order."""
    records: list[tuple[str, int, str, int | None, bool | None, str]] = []
    for input_key in sorted(reaction.inputs):
        reaction_input = reaction.inputs[input_key]
        addition_order = reaction_input.addition_order if reaction_input.addition_order > 0 else None
        for component_ordinal, compound in enumerate(reaction_input.components):
            role = ROLE_ENUM_TO_NAME.get(compound.reaction_role, "other")
            smiles, _ = canonical_smiles(compound.identifiers)
            present, limiting = optional_scalar(compound, "is_limiting")
            records.append(
                (
                    input_key,
                    component_ordinal,
                    role,
                    addition_order,
                    bool(limiting) if present else None,
                    smiles,
                )
            )
    ordered = sorted(
        records,
        key=lambda item: (
            0 if item[4] is True else 1,
            item[3] is None,
            item[3] or 0,
            item[0].encode("utf-8"),
            item[1],
            item[5],
        ),
    )
    result = {role: [] for role in ("reactant", "reagent", "catalyst", "solvent")}
    for _, _, role, _, _, smiles in ordered:
        if role in result:
            result[role].append(smiles)
    return result


def measurement_value(measurement: reaction_pb2.ProductMeasurement) -> tuple[str, bool, float | str | None]:
    """Reproduce the source builder's structured measurement representation."""
    kind = measurement.WhichOneof("value")
    if kind is None:
        return "", False, None
    value = getattr(measurement, kind)
    if kind == "string_value":
        return kind, True, str(value)
    if kind in {"percentage", "float_value"}:
        present, scalar = optional_scalar(value, "value")
        return kind, present, float(str(scalar)) if present else None
    return kind, True, None


def product_records_and_candidates(reaction: reaction_pb2.Reaction) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Project only the product/label evidence needed by the frozen target contract."""
    products: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for outcome_ordinal, outcome in enumerate(reaction.outcomes):
        for product_ordinal, product in enumerate(outcome.products):
            smiles, status = canonical_smiles(product.identifiers)
            desired_present, desired_value = optional_scalar(product, "is_desired_product")
            product_record = {
                "canonical_smiles": smiles,
                "identifier_status": status,
                "is_desired_product_present": desired_present,
                "is_desired_product_value": desired_value,
            }
            products.append(product_record)
            for measurement_ordinal, measurement in enumerate(product.measurements):
                value_kind, value_present, value = measurement_value(measurement)
                candidates.append(
                    {
                        "analysis_key": measurement.analysis_key,
                        "candidate_kind": "product_measurement",
                        "details": measurement.details,
                        "is_desired_product_present": desired_present,
                        "is_desired_product_value": desired_value,
                        "measurement_ordinal": measurement_ordinal,
                        "measurement_type": enum_name(measurement, "type"),
                        "outcome_ordinal": outcome_ordinal,
                        "product_ordinal": product_ordinal,
                        "product_smiles": smiles,
                        "value": value,
                        "value_kind": value_kind,
                        "value_present": value_present,
                    }
                )
    return products, candidates


def pick_product(products: list[dict[str, object]]) -> tuple[str, str]:
    desired = [
        item
        for item in products
        if item["is_desired_product_present"] is True and item["is_desired_product_value"] is True
    ]
    if len(desired) == 1:
        return str(desired[0]["canonical_smiles"]), "unique_desired"
    if not desired and len(products) == 1:
        return str(products[0]["canonical_smiles"]), "unique_product_fallback"
    if len(desired) > 1:
        return "", "multiple_desired_products"
    return "", "ambiguous_product"


def select_unique_percent_yield(reaction: reaction_pb2.Reaction) -> tuple[float | None, str, str, dict[str, object] | None, int]:
    """Apply the original generic target's no-first/no-aggregation label policy."""
    products, candidates = product_records_and_candidates(reaction)
    product_smiles, product_status = pick_product(products)
    if not product_smiles:
        return None, product_smiles, product_status, None, len(candidates)
    eligible = [
        item
        for item in candidates
        if item["candidate_kind"] == "product_measurement"
        and item["measurement_type"] == "YIELD"
        and item["value_kind"] == "percentage"
        and item["value_present"] is True
        and item["product_smiles"] == product_smiles
    ]
    if len(eligible) != 1:
        return None, product_smiles, "missing_label" if not eligible else "ambiguous_label", None, len(candidates)
    candidate = eligible[0]
    value = candidate["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, product_smiles, "non_numeric_label", candidate, len(candidates)
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        return None, product_smiles, "non_finite_label", candidate, len(candidates)
    if not 0.0 <= numeric_value <= 100.0:
        return None, product_smiles, "label_out_of_range", candidate, len(candidates)
    return numeric_value, product_smiles, "unique", candidate, len(candidates)


def unit_projection(message: UnitMessage, target_unit: str) -> float | None:
    present, _ = optional_scalar(message, "value")
    if not present or enum_name(message, "units") == "UNSPECIFIED":
        return None
    try:
        converted = units.UnitResolver().convert(message, target_unit)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return float(converted.value)


def temperature_c(reaction: reaction_pb2.Reaction) -> float | None:
    if not reaction.HasField("conditions") or not reaction.conditions.HasField("temperature"):
        return None
    condition = reaction.conditions.temperature
    if not condition.HasField("setpoint"):
        return None
    return unit_projection(condition.setpoint, "°C")


def reaction_time_s(reaction: reaction_pb2.Reaction) -> float | None:
    values: list[float] = []
    for outcome in reaction.outcomes:
        if not outcome.HasField("reaction_time"):
            continue
        value = unit_projection(outcome.reaction_time, "s")
        if value is None:
            return None
        values.append(value)
    if not values or len({round(value, 12) for value in values}) != 1:
        return None
    return values[0]


def included_decision_id(target_id: str, reaction_key: str, candidate: dict[str, object], value: float, contract: dict[str, object]) -> str:
    payload = {
        "adapter": "generic",
        "adapter_version": contract["adapter_version"],
        "candidate": candidate,
        "reaction_key": reaction_key,
        "target_id": target_id,
        "value": value,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def source_links(source_rows: list[dict[str, str]], logical_id: str) -> dict[str, object]:
    return {
        "schema_version": VERSION,
        "logical_dataset_id": logical_id,
        "source_manifest_path": "provenance/source-files.initial.csv",
        "links": [
            {
                "physical_dataset_id": row["physical_dataset_id"],
                "source_file": row["upstream_path"],
                "upstream_revision": row["upstream_revision"],
                "source_file_url": row["source_file_url"],
                "source_sha256": row["source_sha256"],
                "git_lfs_oid": row["git_lfs_oid"],
                "size_bytes": int(row["size_bytes"]),
                "reaction_count": int(row["reaction_count"]),
                "data_license_id": row["data_license_id"],
                "verification_status": row["verification_status"],
            }
            for row in sorted(source_rows, key=lambda item: item["upstream_path"])
        ],
    }


def write_checksums(directory: Path, names: dict[str, str]) -> None:
    rows = []
    for role, name in names.items():
        path = directory / name
        rows.append({"role": role, "path": name, "sha256": sha256(path), "size_bytes": path.stat().st_size})
    write_csv(directory / "checksums.csv", ["role", "path", "sha256", "size_bytes"], rows)


def build_percent_yield_target(
    corpus_csv: Path,
    target: dict[str, str],
    source_rows: list[dict[str, str]],
    target_root: Path,
    schema_dir: Path,
    source_manifest_hash: str,
) -> dict[str, object]:
    if target["label_type"] != "reaction_yield_percent" or target["target_adapter"] != "generic":
        raise ValueError("clean-room adapter currently supports only generic reaction_yield_percent targets")
    contract = TARGET_CONTRACTS.get(target["target_id"])
    if contract is None:
        raise ValueError(f"no frozen standardized target contract is available for {target['target_id']}")
    columns = list(contract["columns"])
    if target["label_column"] not in columns or columns[-1] != target["label_column"]:
        raise ValueError("frozen target contract and semantic target map disagree on label serialization")
    target_sources = set(parse_json_array(target, "physical_dataset_ids_json"))
    if len(target_sources) != 1:
        raise ValueError("clean-room percent-yield adapter requires exactly one physical target source")
    selected_sources = [row for row in source_rows if row["physical_dataset_id"] in target_sources]
    if len(selected_sources) != 1:
        raise ValueError("target source is missing from the rebuilt logical corpus")
    slug = target["target_slug"]
    final_dir = target_root / slug
    partial_dir = target_root / f".{slug}.partial"
    if final_dir.exists() or partial_dir.exists():
        raise FileExistsError(f"refusing to overwrite model-ready target: {slug}")
    partial_dir.mkdir(parents=True)
    label_column = target["label_column"]
    included_records: list[dict[str, object]] = []
    row_map: list[dict[str, object]] = []
    exclusions: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    try:
        with corpus_csv.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != CORPUS_HEADER:
                raise ValueError("rebuilt corpus CSV has an unexpected header")
            for row in reader:
                if row["physical_dataset_id"] not in target_sources:
                    continue
                reaction = reaction_pb2.Reaction()
                try:
                    ParseDict(json.loads(row["reaction_json"]), reaction, ignore_unknown_fields=False)
                except (TypeError, ValueError) as error:
                    raise ValueError(f"corpus reaction JSON cannot be parsed: {row['reaction_id']}") from error
                if reaction.reaction_id != row["reaction_id"]:
                    raise ValueError("corpus reaction JSON disagrees with reaction_id")
                reaction_key = f"{row['physical_dataset_id']}:{row['reaction_id']}"
                components = collect_components(reaction)
                role_limits = contract["role_limits"]
                if not isinstance(role_limits, dict):
                    raise TypeError("target role limits are invalid")
                for role, limit in role_limits.items():
                    if len(components[role]) > limit:
                        raise ValueError(f"target projection schema overflow for {reaction_key}: {role}")
                value, product_smiles, reason, candidate, candidate_count = select_unique_percent_yield(reaction)
                temperature = temperature_c(reaction)
                duration = reaction_time_s(reaction)
                if not any(components["reactant"]):
                    value = None
                    reason = "missing_valid_reactant"
                elif value is not None and (temperature is None or duration is None):
                    value = None
                    reason = "missing_or_invalid_required_numeric_condition"
                if value is None:
                    decision = "excluded"
                    decision_value = ""
                    exclusions.append(
                        {
                            "reaction_key": reaction_key,
                            "physical_dataset_id": row["physical_dataset_id"],
                            "source_row_index": row["row_index"],
                            "reason": reason,
                            "candidate_count": candidate_count,
                        }
                    )
                else:
                    if candidate is None or temperature is None or duration is None:
                        raise RuntimeError("included target row is missing projection evidence")
                    decision = "included"
                    decision_value = included_decision_id(target["target_id"], reaction_key, candidate, value, contract)
                    feature_row: dict[str, object] = {column: "" for column in columns}
                    for role, limit in role_limits.items():
                        for ordinal, smiles in enumerate(components[role], start=1):
                            feature_row[f"{role}-{ordinal}"] = smiles
                    feature_row["product"] = product_smiles
                    feature_row["temperature_c"] = temperature
                    feature_row["reaction_time_s"] = duration
                    feature_row[label_column] = value
                    included_records.append(
                        {
                            "feature_row": {column: feature_row[column] for column in columns},
                            "physical_dataset_id": row["physical_dataset_id"],
                            "reaction_id": row["reaction_id"],
                            "source_row_index": int(row["row_index"]),
                            "reaction_key": reaction_key,
                            "label_decision_id": decision_value,
                        }
                    )
                audit.append(
                    {
                        "adapter_version": contract["adapter_version"],
                        "candidate_count": candidate_count,
                        "label_column": label_column,
                        "label_decision_id": decision_value,
                        "physical_dataset_id": row["physical_dataset_id"],
                        "product_smiles": product_smiles,
                        "reaction_key": reaction_key,
                        "reason": reason,
                        "selected_candidate": candidate,
                        "source_row_index": int(row["row_index"]),
                        "status": decision,
                        "target_adapter": "generic",
                        "target_id": target["target_id"],
                        "value": value,
                    }
                )
        expected_source_count = int(target["source_count"])
        if len(included_records) + len(exclusions) != expected_source_count:
            raise ValueError("target source count differs from frozen semantic target map")
        if len(included_records) != int(target["included_count"]) or len(exclusions) != int(target["excluded_count"]):
            raise ValueError("clean-room target decisions differ from frozen semantic target map")
        included_records.sort(
            key=lambda item: (item["physical_dataset_id"], item["reaction_id"], item["source_row_index"])
        )
        audit.sort(key=lambda item: (str(item["physical_dataset_id"]), str(item["reaction_key"])))
        for csv_row_number, record in enumerate(included_records, start=2):
            row_map.append(
                {
                    "csv_row_number": csv_row_number,
                    "reaction_key": record["reaction_key"],
                    "physical_dataset_id": record["physical_dataset_id"],
                    "source_row_index": record["source_row_index"],
                    "label_decision_id": record["label_decision_id"],
                }
            )
        write_csv(partial_dir / "dataset.csv", columns, [record["feature_row"] for record in included_records])
        write_csv(
            partial_dir / "row-map.csv",
            ["csv_row_number", "reaction_key", "physical_dataset_id", "source_row_index", "label_decision_id"],
            row_map,
        )
        write_csv(
            partial_dir / "exclusions.csv",
            ["reaction_key", "physical_dataset_id", "source_row_index", "reason", "candidate_count"],
            exclusions,
        )
        with (partial_dir / "audit.jsonl").open("w", encoding="utf-8") as handle:
            for item in audit:
                handle.write(canonical_json(item) + "\n")
        target_schema = {
            "schema_version": VERSION,
            "dataset_kind": "model-ready",
            "target_id": target["target_id"],
            "columns": columns,
            "column_roles": contract["column_roles"],
            "label_policy": target["label_policy"],
            "adapter": "generic",
            "adapter_version": contract["adapter_version"],
            "project_name": contract["project_name"],
        }
        write_json(partial_dir / "schema.json", target_schema)
        links = source_links(selected_sources, target["logical_dataset_id"])
        Draft202012Validator(json.loads((schema_dir / "source-links.schema.json").read_text(encoding="utf-8"))).validate(links)
        write_json(partial_dir / "source-links.json", links)
        target_provenance = {
            "schema_version": VERSION,
            "target_id": target["target_id"],
            "input": {"corpus_csv_sha256": sha256(corpus_csv), "source_manifest_sha256": source_manifest_hash},
            "transformation": {
                "name": "generic_standardized_percent_yield_projection",
                "policy": target["label_policy"],
                "candidate_measurement_type": "YIELD",
                "row_order": "physical_dataset_id,reaction_id,source_row_index",
                "structure_policy": "SMILES>CXSMILES>InChI>MOLBLOCK;rdkit_canonical_isomeric;no_fragment_split",
            },
            "counts": {"included": len(included_records), "excluded": len(exclusions), "source": expected_source_count},
        }
        write_json(partial_dir / "target-provenance.json", target_provenance)
        checksum_names = {
            "dataset": "dataset.csv",
            "schema": "schema.json",
            "row-map": "row-map.csv",
            "exclusions": "exclusions.csv",
            "audit": "audit.jsonl",
            "source-links": "source-links.json",
            "target-provenance": "target-provenance.json",
        }
        write_checksums(partial_dir, checksum_names)
        metadata_artifacts = []
        for role in ("dataset", "schema", "row-map", "exclusions", "audit"):
            path = partial_dir / checksum_names[role]
            metadata_artifacts.append(
                {"role": role, "path": f"datasets/model-ready/{slug}/{path.name}", "sha256": sha256(path), "size_bytes": path.stat().st_size}
            )
        checksum_path = partial_dir / "checksums.csv"
        metadata_artifacts.append(
            {"role": "checksums", "path": f"datasets/model-ready/{slug}/checksums.csv", "sha256": sha256(checksum_path), "size_bytes": checksum_path.stat().st_size}
        )
        metadata = {
            "schema_version": VERSION,
            "dataset_kind": "model-ready",
            "dataset_slug": slug,
            "display_name_en": target["display_name_en"],
            "display_name_zh": target["display_name_zh"],
            "logical_dataset_id": target["logical_dataset_id"],
            "physical_dataset_ids": sorted(target_sources),
            "source_links_path": f"datasets/model-ready/{slug}/source-links.json",
            "license_id": "CC-BY-SA-4.0",
            "artifact_status": "staged",
            "readiness_status": target["readiness_status"],
            "corpus_row_count": int(target["source_count"]),
            "target_id": target["target_id"],
            "label": {"column": label_column, "type": target["label_type"], "unit": target["label_unit"], "policy": target["label_policy"]},
            "included_count": len(included_records),
            "excluded_count": len(exclusions),
            "content_artifacts": metadata_artifacts,
            "input_provenance": {
                "ord_upstream_revision": selected_sources[0]["upstream_revision"],
                "source_manifest_sha256": source_manifest_hash,
                "semantic_name_policy_version": target["naming_policy_version"],
                "provenance_schema_version": VERSION,
                "pipeline_commit": None,
            },
        }
        Draft202012Validator(json.loads((schema_dir / "dataset-metadata.schema.json").read_text(encoding="utf-8"))).validate(metadata)
        write_json(partial_dir / "metadata.json", metadata)
        os.replace(partial_dir, final_dir)
    except Exception:
        if partial_dir.exists():
            shutil.rmtree(partial_dir)
        raise
    return {
        "target_id": target["target_id"],
        "target_slug": slug,
        "included_count": len(included_records),
        "excluded_count": len(exclusions),
        "artifacts": {path.name: {"sha256": sha256(path), "size_bytes": path.stat().st_size} for path in sorted(final_dir.iterdir()) if path.is_file()},
    }


def output_tree(root: Path) -> tuple[list[dict[str, object]], str]:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "clean-room-output-manifest.json"):
        records.append({"path": path.relative_to(root).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size})
    root_hash = hashlib.sha256(canonical_json(records).encode("utf-8")).hexdigest()
    return records, root_hash


def find_single(rows: list[dict[str, str]], field: str, value: str, label: str) -> dict[str, str]:
    matches = [row for row in rows if row.get(field) == value]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label} with {field}={value}, found {len(matches)}")
    return matches[0]


def baseline_comparison(
    corpus_manifest_path: Path | None, target_manifest_path: Path | None, physical_index_path: Path | None,
    logical: dict[str, str], target: dict[str, str], physical_records: list[dict[str, object]], corpus_hash: str,
    target_record: dict[str, object],
) -> dict[str, object]:
    """Compare only control-plane hashes; never read a local payload or cache."""
    result: dict[str, object] = {"available": False}
    if physical_index_path is not None:
        physical_rows = read_csv(physical_index_path)
        matches = [row for row in physical_rows if row.get("old_path", "").endswith(f"{physical_records[0]['physical_dataset_id']}.csv")]
        if len(matches) != 1:
            raise ValueError("physical archive index has no unique selected source record")
        expected = matches[0]["sha256"]
        result["physical_csv"] = {"expected_sha256": expected, "actual_sha256": physical_records[0]["sha256"], "matches": expected == physical_records[0]["sha256"]}
    if corpus_manifest_path is not None:
        corpus_manifest = json.loads(corpus_manifest_path.read_text(encoding="utf-8"))
        package = find_single(corpus_manifest["packages"], "dataset_slug", logical["directory_slug"], "baseline corpus package")
        expected = package["reaction_sha256"]
        result["corpus"] = {"expected_reactions_sha256": expected, "actual_reactions_sha256": corpus_hash, "matches": expected == corpus_hash, "row_count_matches": int(package["row_count"]) == int(logical["reaction_count"])}
    if target_manifest_path is not None:
        target_manifest = json.loads(target_manifest_path.read_text(encoding="utf-8"))
        package = find_single(target_manifest["packages"], "target_id", target["target_id"], "baseline target package")
        expected = package["artifacts"]["dataset.csv"]["sha256"]
        actual = target_record["artifacts"]["dataset.csv"]["sha256"]
        result["target"] = {
            "expected_dataset_sha256": expected,
            "actual_dataset_sha256": actual,
            "dataset_bytes_match": expected == actual,
            "included_count_matches": int(package["included_count"]) == int(target_record["included_count"]),
            "excluded_count_matches": int(package["excluded_count"]) == int(target_record["excluded_count"]),
            "source_count_matches": int(package["source_count"]) == int(target_record["included_count"]) + int(target_record["excluded_count"]),
        }
    result["available"] = any(key in result for key in ("physical_csv", "corpus", "target"))
    return result


def run(
    source_manifest_path: Path,
    semantic_map_path: Path,
    members_path: Path,
    target_map_path: Path,
    schema_dir: Path,
    physical_id: str,
    target_id: str,
    download_root: Path,
    output_root: Path,
    report_path: Path,
    timeout_seconds: int = 300,
    baseline_corpus_manifest_path: Path | None = None,
    baseline_target_manifest_path: Path | None = None,
    baseline_physical_index_path: Path | None = None,
    expected_output_root_sha256: str | None = None,
) -> dict[str, object]:
    if is_within(download_root, output_root) or is_within(output_root, download_root):
        raise ValueError("download root and output root must not contain one another")
    if is_within(download_root, Path.cwd()):
        raise ValueError("download root must be outside the repository working directory")
    nonempty_clean_directory(download_root, "download root")
    nonempty_clean_directory(output_root, "clean-room output root")
    if is_within(report_path, output_root):
        raise ValueError("report path must be outside clean-room output root")
    source_rows = read_csv(source_manifest_path)
    target_rows = read_csv(target_map_path)
    target = find_single(target_rows, "target_id", target_id, "target")
    target_source_ids = parse_json_array(target, "physical_dataset_ids_json")
    if physical_id not in target_source_ids:
        raise ValueError("selected physical ID is not declared by selected target")
    selected_source = find_single(source_rows, "physical_dataset_id", physical_id, "source")
    logical = find_single(read_csv(semantic_map_path), "logical_dataset_id", target["logical_dataset_id"], "logical dataset")
    members = [row for row in read_csv(members_path) if row["logical_dataset_id"] == logical["logical_dataset_id"]]
    if not members:
        raise ValueError("selected logical dataset has no physical members")
    source_by_id = {row["physical_dataset_id"]: row for row in source_rows}
    logical_sources = []
    for member in members:
        source = source_by_id.get(member["physical_dataset_id"])
        if source is None or source["upstream_path"] != member["source_file"]:
            raise ValueError("logical membership and source manifest disagree")
        logical_sources.append(source)
    if selected_source not in logical_sources:
        raise ValueError("selected target source is not a member of its logical corpus")
    if int(logical["reaction_count"]) != sum(int(member["reaction_count"]) for member in members):
        raise ValueError("logical corpus count disagrees with membership")

    provenance_root = output_root / "provenance"
    physical_root = output_root / "physical"
    logical_root = output_root / "logical"
    corpus_root = output_root / "datasets" / "corpus"
    target_root = output_root / "datasets" / "model-ready"
    for directory in (provenance_root, physical_root, logical_root, corpus_root, target_root):
        directory.mkdir(parents=True, exist_ok=True)
    write_csv(provenance_root / "source-files.initial.csv", list(source_rows[0]), logical_sources)
    write_csv(provenance_root / "logical-dataset-members.csv", list(members[0]), members)
    write_csv(provenance_root / "semantic-name-map.csv", list(logical), [logical])
    write_csv(provenance_root / "semantic-target-map.csv", list(target), [target])
    source_manifest_hash = sha256(provenance_root / "source-files.initial.csv")

    download_records = []
    physical_records = []
    physical_csvs: list[tuple[dict[str, str], Path]] = []
    for source in sorted(logical_sources, key=lambda row: row["upstream_path"]):
        download = download_lfs_source(source, download_root, timeout_seconds)
        download_records.append({key: value for key, value in download.items() if key != "path"})
        physical_csv = physical_root / f"{source['physical_dataset_id']}.csv"
        physical_records.append(parquet_to_physical_csv(download["path"], source, physical_csv))
        physical_csvs.append((source, physical_csv))
    logical_csv = logical_root / f"logical_dataset_id={logical['logical_dataset_id']}" / "reactions.csv"
    logical_csv.parent.mkdir(parents=True)
    logical_record = assemble_logical_csv(physical_csvs, logical_csv)
    if logical_record["row_count"] != int(logical["reaction_count"]):
        raise ValueError("assembled logical CSV row count differs from semantic map")

    corpus_run_manifest = provenance_root / "corpus-build-manifest.json"
    corpus_summary = build_corpus(
        logical_root,
        provenance_root / "semantic-name-map.csv",
        provenance_root / "logical-dataset-members.csv",
        provenance_root / "source-files.initial.csv",
        corpus_root,
        provenance_root / "redaction-audits",
        corpus_run_manifest,
        schema_dir,
        expected_corpus_count=1,
        expected_reaction_count=int(logical["reaction_count"]),
        expected_physical_count=len(logical_sources),
    )
    corpus_dir = corpus_root / logical["directory_slug"]
    target_record = build_percent_yield_target(
        corpus_dir / "reactions.csv", target, logical_sources, target_root, schema_dir, source_manifest_hash
    )
    transformations = [
        {"schema_version": VERSION, "step": "public_lfs_to_physical_csv", "inputs": [item["source_sha256"] for item in download_records], "outputs": [item["sha256"] for item in physical_records]},
        {"schema_version": VERSION, "step": "physical_csv_to_logical_corpus", "inputs": [item["sha256"] for item in physical_records], "outputs": [logical_record["sha256"], sha256(corpus_dir / "reactions.csv")]},
        {"schema_version": VERSION, "step": "logical_corpus_to_model_ready_target", "inputs": [sha256(corpus_dir / "reactions.csv")], "outputs": [target_record["artifacts"]["dataset.csv"]["sha256"]]},
    ]
    with (provenance_root / "transformations.jsonl").open("w", encoding="utf-8") as handle:
        for record in transformations:
            handle.write(canonical_json(record) + "\n")
    files, root_hash = output_tree(output_root)
    output_manifest = {"schema_version": VERSION, "files": files, "root_sha256": root_hash}
    write_json(output_root / "clean-room-output-manifest.json", output_manifest)
    if expected_output_root_sha256 is not None and (
        len(expected_output_root_sha256) != 64 or any(character not in "0123456789abcdef" for character in expected_output_root_sha256)
    ):
        raise ValueError("expected output root SHA-256 must be lowercase hexadecimal")
    corpus_hash = sha256(corpus_dir / "reactions.csv")
    baseline = baseline_comparison(
        baseline_corpus_manifest_path,
        baseline_target_manifest_path,
        baseline_physical_index_path,
        logical,
        target,
        physical_records,
        corpus_hash,
        target_record,
    )
    byte_gate = baseline.get("target", {}).get("dataset_bytes_match")
    repeat_matches = expected_output_root_sha256 is None or expected_output_root_sha256 == root_hash
    if byte_gate not in (None, True):
        status = "partial_target_byte_equivalence_unresolved"
    elif not repeat_matches:
        status = "failed_repeat_hash_mismatch"
    else:
        status = "complete"
    report = {
        "schema_version": VERSION,
        "step_id": "step-20",
        "status": status,
        "clean_room_policy": {
            "public_input_only": True,
            "local_staging_or_cache_used_as_input": False,
            "original_parquet_written_inside_repository": False,
            "download_root_must_be_external": True,
        },
        "sample": {
            "selected_physical_dataset_id": physical_id,
            "logical_dataset_id": logical["logical_dataset_id"],
            "corpus_slug": logical["directory_slug"],
            "target_id": target_id,
            "target_slug": target["target_slug"],
        },
        "public_source_retrieval": download_records,
        "physical_csv": physical_records,
        "logical_csv": logical_record,
        "corpus": {"summary": corpus_summary, "reactions_sha256": corpus_hash},
        "target": target_record,
        "provenance": {"source_manifest_sha256": source_manifest_hash, "transformations_path": "provenance/transformations.jsonl"},
        "reproducibility": {"output_file_count": len(files), "output_root_sha256": root_hash, "output_manifest_path": "clean-room-output-manifest.json"},
        "independent_repeat": None
        if expected_output_root_sha256 is None
        else {"expected_output_root_sha256": expected_output_root_sha256, "matches": expected_output_root_sha256 == root_hash},
        "baseline_comparison": baseline,
        "remaining_blocker": (
            None
            if status == "complete"
            else "The extracted standardized target projection has matching source/included/excluded semantics but does not byte-match the frozen target dataset artifact."
            if status == "partial_target_byte_equivalence_unresolved"
            else "The independently repeated clean-room output root hash differs from the expected hash."
        ),
    }
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--semantic-map", required=True, type=Path)
    parser.add_argument("--members", required=True, type=Path)
    parser.add_argument("--target-map", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--physical-id", required=True)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--download-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--report-path", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--baseline-corpus-manifest", type=Path)
    parser.add_argument("--baseline-target-manifest", type=Path)
    parser.add_argument("--baseline-physical-index", type=Path)
    parser.add_argument("--expected-output-root-sha256")
    args = parser.parse_args()
    result = run(
        source_manifest_path=args.source_manifest,
        semantic_map_path=args.semantic_map,
        members_path=args.members,
        target_map_path=args.target_map,
        schema_dir=args.schema_dir,
        physical_id=args.physical_id,
        target_id=args.target_id,
        download_root=args.download_root,
        output_root=args.output_root,
        report_path=args.report_path,
        timeout_seconds=args.timeout_seconds,
        baseline_corpus_manifest_path=args.baseline_corpus_manifest,
        baseline_target_manifest_path=args.baseline_target_manifest,
        baseline_physical_index_path=args.baseline_physical_index,
        expected_output_root_sha256=args.expected_output_root_sha256,
    )
    print(json.dumps({"status": result["status"], "output_root_sha256": result["reproducibility"]["output_root_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
