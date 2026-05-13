"""BIM / IFC ingestion routes.

The MVP focuses on local IFC files:
IFC upload -> element/quantity extraction -> RAG chunks -> Chroma indexing.
"""

import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import get_rag_service
from api.schemas import UploadResponse
from services.rag_service import RAGService

router = APIRouter(prefix="/bim", tags=["bim"])


TARGET_CLASSES = [
    "IfcWall",
    "IfcSlab",
    "IfcBeam",
    "IfcColumn",
    "IfcDoor",
    "IfcWindow",
    "IfcRoof",
    "IfcStair",
    "IfcRailing",
    "IfcFooting",
    "IfcPile",
    "IfcBuildingElementProxy",
]


def _require_ifcopenshell():
    try:
        import ifcopenshell
        import ifcopenshell.util.element as ifc_element
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "IFC parsing requires ifcopenshell. Install it with: "
                "py -3.13 -m pip install ifcopenshell"
            ),
        ) from e
    return ifcopenshell, ifc_element


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _extract_quantities(element: Any) -> Dict[str, Optional[float]]:
    quantities = {"volume_m3": None, "area_m2": None, "length_m": None}
    try:
        for rel in getattr(element, "IsDefinedBy", []) or []:
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            definition = rel.RelatingPropertyDefinition
            if not definition.is_a("IfcElementQuantity"):
                continue
            for qty in definition.Quantities:
                name = (qty.Name or "").lower()
                if "volume" in name and hasattr(qty, "VolumeValue"):
                    quantities["volume_m3"] = _safe_float(qty.VolumeValue)
                elif "area" in name and hasattr(qty, "AreaValue"):
                    quantities["area_m2"] = _safe_float(qty.AreaValue)
                elif "length" in name and hasattr(qty, "LengthValue"):
                    quantities["length_m"] = _safe_float(qty.LengthValue)
    except Exception:
        pass
    return quantities


def _extract_properties(element: Any, limit: int = 20) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    try:
        for rel in getattr(element, "IsDefinedBy", []) or []:
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            definition = rel.RelatingPropertyDefinition
            if not definition.is_a("IfcPropertySet"):
                continue
            for prop in definition.HasProperties:
                if len(props) >= limit:
                    return props
                value = getattr(prop, "NominalValue", None)
                if value is not None and hasattr(value, "wrappedValue"):
                    props[prop.Name] = value.wrappedValue
    except Exception:
        pass
    return props


def _material_name(element: Any, ifc_element: Any) -> str:
    try:
        material = ifc_element.get_material(element)
        if not material:
            return ""
        if hasattr(material, "Name"):
            return material.Name or ""
        if hasattr(material, "MaterialLayers") and material.MaterialLayers:
            first = material.MaterialLayers[0]
            return getattr(first.Material, "Name", "") or ""
    except Exception:
        return ""
    return ""


def _level_name(element: Any, ifc_element: Any) -> str:
    try:
        container = ifc_element.get_container(element)
        return getattr(container, "Name", "") or ""
    except Exception:
        return ""


def parse_ifc_bytes(content: bytes) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ifcopenshell, ifc_element = _require_ifcopenshell()

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        model = ifcopenshell.open(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    elements: List[Dict[str, Any]] = []
    by_class: Counter[str] = Counter()
    by_material: Counter[str] = Counter()
    by_level: Counter[str] = Counter()
    total_volume = 0.0
    total_area = 0.0
    total_length = 0.0

    for ifc_class in TARGET_CLASSES:
        for element in model.by_type(ifc_class):
            quantities = _extract_quantities(element)
            material = _material_name(element, ifc_element)
            level = _level_name(element, ifc_element)

            volume = quantities["volume_m3"] or 0.0
            area = quantities["area_m2"] or 0.0
            length = quantities["length_m"] or 0.0
            total_volume += volume
            total_area += area
            total_length += length

            by_class[ifc_class] += 1
            if material:
                by_material[material] += 1
            if level:
                by_level[level] += 1

            elements.append({
                "guid": getattr(element, "GlobalId", ""),
                "ifc_class": ifc_class,
                "name": getattr(element, "Name", "") or ifc_class,
                "level": level,
                "material": material,
                **quantities,
                "properties": _extract_properties(element),
            })

    summary = {
        "total_elements": len(elements),
        "by_class": dict(by_class.most_common()),
        "by_material": dict(by_material.most_common(20)),
        "by_level": dict(by_level.most_common()),
        "total_volume_m3": round(total_volume, 3),
        "total_area_m2": round(total_area, 3),
        "total_length_m": round(total_length, 3),
    }
    return elements, summary


def _build_bim_chunks(
    filename: str,
    elements: List[Dict[str, Any]],
    summary: Dict[str, Any],
    project: str,
    lot: str,
    auteur: str,
    criticite: str,
) -> List[Dict[str, Any]]:
    ingested_at = datetime.utcnow().isoformat()
    source = f"[BIM] {filename}"
    chunks: List[Dict[str, Any]] = []

    summary_text = [
        f"BIM IFC MODEL: {filename}",
        f"Project: {project}",
        f"Lot: {lot}",
        f"Total elements: {summary['total_elements']}",
        f"Total volume m3: {summary['total_volume_m3']}",
        f"Total area m2: {summary['total_area_m2']}",
        f"Total length m: {summary['total_length_m']}",
        "",
        "Elements by IFC class:",
        *[f"- {key}: {value}" for key, value in summary["by_class"].items()],
        "",
        "Main materials:",
        *[f"- {key}: {value}" for key, value in summary["by_material"].items()],
        "",
        "Levels:",
        *[f"- {key}: {value}" for key, value in summary["by_level"].items()],
    ]

    chunks.append({
        "text": "\n".join(summary_text).strip(),
        "metadata": {
            "source": source,
            "project": project,
            "lot": lot,
            "auteur": auteur,
            "criticite": criticite,
            "file_type": "bim",
            "bim_format": "ifc",
            "ingested_at": ingested_at,
            "chunk_index": 0,
        },
    })

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for element in elements:
        grouped[element["ifc_class"]].append(element)

    for ifc_class, class_elements in grouped.items():
        lines = [
            f"BIM IFC ELEMENTS - {ifc_class}",
            f"Source model: {filename}",
            f"Count: {len(class_elements)}",
            "",
        ]
        for element in class_elements[:80]:
            q = []
            if element.get("volume_m3"):
                q.append(f"volume={element['volume_m3']} m3")
            if element.get("area_m2"):
                q.append(f"area={element['area_m2']} m2")
            if element.get("length_m"):
                q.append(f"length={element['length_m']} m")
            details = ", ".join(q) if q else "no quantities"
            lines.append(
                f"- {element['name']} | guid={element['guid']} | "
                f"level={element.get('level') or ''} | material={element.get('material') or ''} | {details}"
            )

        chunks.append({
            "text": "\n".join(lines).strip(),
            "metadata": {
                "source": source,
                "project": project,
                "lot": lot,
                "auteur": auteur,
                "criticite": criticite,
                "file_type": "bim",
                "bim_format": "ifc",
                "ifc_class": ifc_class,
                "ingested_at": ingested_at,
                "chunk_index": len(chunks),
            },
        })

    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks
    return chunks


@router.post("/ifc/upload", response_model=UploadResponse)
async def upload_ifc_model(
    file: UploadFile = File(...),
    project: str = Form(""),
    lot: str = Form(""),
    auteur: str = Form(""),
    criticite: str = Form("Normale"),
    rag: RAGService = Depends(get_rag_service),
):
    """Parse and index an IFC model into the vector store."""
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Only .ifc files are supported.")

    content = await file.read()
    elements, summary = parse_ifc_bytes(content)
    if not elements:
        raise HTTPException(status_code=400, detail="No supported BIM elements found in this IFC file.")

    chunks = _build_bim_chunks(
        filename=file.filename,
        elements=elements,
        summary=summary,
        project=project,
        lot=lot,
        auteur=auteur,
        criticite=criticite,
    )
    count = rag.add_documents(chunks)
    return UploadResponse(
        filename=file.filename,
        chunks=count,
        status="success",
        message=(
            f"Indexed {summary['total_elements']} BIM elements "
            f"across {len(summary['by_class'])} IFC classes"
        ),
    )


@router.post("/ifc/summary")
async def summarize_ifc_model(file: UploadFile = File(...)):
    """Parse an IFC model and return a structured summary without indexing."""
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Only .ifc files are supported.")

    elements, summary = parse_ifc_bytes(await file.read())
    return {
        "filename": file.filename,
        "summary": summary,
        "sample_elements": elements[:25],
    }
