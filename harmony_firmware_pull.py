#!/usr/bin/env python3
"""Download Logitech Harmony firmware bundles from SUS.

This helper is intentionally boring: it uses only Python's standard library,
works on Windows/Linux/macOS, and writes the same kind of firmware pull folder
we used while mapping Harmony product/skin IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUS_ENDPOINT = "https://sus.dhg.myharmony.com/SoftwareUpdatesPlatform/SoftwareUpdates/getUpdates"
CLOUDFRONT_BASE = "https://d3pk1wwd3l8fri.cloudfront.net/sus/images"
S3_BASE = "https://dhg-prod-sus-suss3bucket-1d3ewoswtrcur.s3.amazonaws.com/sus/images"
SUS_KEY = "UV6nr6k8ZqlLYksPWMOlv5qwNU2lo1j8Q57WgwE5"

SHA_HUB_415600 = "9eda076d10f32256221fbde3dd3e9ca839a720c2b96939a9c265c198a0f8029d"
SHA_HANDHELD_415330 = "9bc098744943e86d8b6ddbbd75633ca2bc05970eaa42787b81fa8aa6ef1ed652"

KNOWN_PRODUCTS: dict[str, dict[str, Any]] = {
    "97": {
        "firmware": "4.15.600",
        "file": "4.15.600.2987731.hfw2",
        "pathProductId": "106",
        "product": "Harmony Hub",
        "codename": "Pimento",
        "role": "Hub",
        "confidence": "confirmed",
        "size": 4771065,
        "sha256": SHA_HUB_415600,
        "note": "Shared hub bundle; Description.xml declares intended skins 97, 106, and 109.",
    },
    "99": {
        "firmware": "4.15.330",
        "file": "4.15.330.712524.hfw2",
        "product": "Harmony Touch",
        "codename": "Juniper",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "100": {
        "firmware": "4.15.330",
        "file": "4.15.330.5773985.hfw2",
        "product": "Harmony Ultimate",
        "codename": "JuniperRF / Olive alias",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "102": {
        "firmware": "4.15.330",
        "file": "4.15.330.8596752.hfw2",
        "product": "Harmony Ultimate One",
        "codename": "Bulliet / Ultimate One",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "105": {
        "firmware": "4.15.330",
        "file": "4.15.330.7346716.hfw2",
        "product": "Harmony Ultimate Home",
        "codename": "NewCastle",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "106": {
        "firmware": "4.15.600",
        "file": "4.15.600.2987731.hfw2",
        "product": "Harmony Home Hub",
        "codename": "Creemore",
        "role": "Hub",
        "confidence": "confirmed",
        "size": 4771065,
        "sha256": SHA_HUB_415600,
    },
    "108": {
        "firmware": "4.15.330",
        "file": "4.15.330.1416643.hfw2",
        "product": "Harmony Ultimate Home",
        "codename": "NewCastleWhite",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "109": {
        "firmware": "4.15.600",
        "file": "4.15.600.2987731.hfw2",
        "pathProductId": "106",
        "product": "Unresolved Harmony hub variant",
        "codename": "unresolved",
        "role": "Hub",
        "confidence": "target skin confirmed, name unresolved",
        "size": 4771065,
        "sha256": SHA_HUB_415600,
        "note": "SUS direct lookup for 109 may not publish its own row; the hub bundle declares skin 109.",
    },
    "111": {
        "firmware": "4.15.330",
        "file": "4.15.330.6905402.hfw2",
        "product": "Harmony Elite / Harmony Pro",
        "codename": "Hops",
        "role": "Handheld remote",
        "confidence": "confirmed; depends on Pro SKU flag",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "112": {
        "firmware": "4.15.330",
        "file": "4.15.330.8196409.hfw2",
        "product": "Harmony 950",
        "codename": "HopsLite",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13041774,
        "sha256": SHA_HANDHELD_415330,
    },
    "115": {
        "firmware": "10.0.230",
        "file": "10.0.230.1601641.hfw2",
        "product": "Harmony Pro 2400 Hub",
        "codename": "Crackerjack",
        "role": "Hub",
        "confidence": "confirmed codename and role",
        "size": 4773033,
        "sha256": "01dedf3ec2b66ea4cbd28515f5c681b79731b927f732d1f73a6520c2e52ef888",
    },
    "116": {
        "firmware": "10.0.215",
        "file": "10.0.215.6483963.hfw2",
        "product": "Harmony Pro 2400 Remote",
        "codename": "Orville",
        "role": "Handheld remote",
        "confidence": "confirmed",
        "size": 13042989,
        "sha256": "3116ab02e8bf5314f2ae32ff1afba92327542f5c7e75963b3da0bf34afd34e66",
    },
}


class FirmwarePullError(RuntimeError):
    """Raised for expected command-line failures."""


def json_dump(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json_dump(data) + "\n", encoding="utf-8")


def known_url(product_id: str, prefer_s3: bool) -> str:
    entry = KNOWN_PRODUCTS[product_id]
    path_product_id = entry.get("pathProductId", product_id)
    base = S3_BASE if prefer_s3 else CLOUDFRONT_BASE
    return f"{base}/{path_product_id}/{entry['file']}"


def known_update(product_id: str) -> dict[str, Any]:
    if product_id not in KNOWN_PRODUCTS:
        raise FirmwarePullError(f"product/skin {product_id} is not in the known firmware table")

    entry = KNOWN_PRODUCTS[product_id]
    return {
        "source": "known",
        "id": entry["firmware"],
        "productId": product_id,
        "file": entry["file"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "uri": known_url(product_id, prefer_s3=False),
        "uri2": known_url(product_id, prefer_s3=True),
        "knownProduct": entry,
    }


def request_sus_update(product_id: str, args: argparse.Namespace) -> dict[str, Any]:
    unit_id = args.unit_id or f"codex-tool-{product_id}"
    master_unit_id = args.master_unit_id or unit_id
    request_body = {
        "requests": [
            {
                "name": "base",
                "channel": args.channel,
                "criticalOnly": False,
                "sysBuild": args.sys_build,
                "unitId": unit_id,
                "masterUnitId": master_unit_id,
                "productId": product_id,
                "masterProductId": product_id,
                "pairings": [],
                "trigger": "manual",
            }
        ]
    }
    raw_body = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        SUS_ENDPOINT,
        data=raw_body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Logitech-SUS-Key": SUS_KEY,
            "User-Agent": "harmony-firmware-pull/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response_body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise FirmwarePullError(f"SUS lookup for {product_id} failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise FirmwarePullError(f"SUS lookup for {product_id} failed: {exc.reason}") from exc

    try:
        document = json.loads(response_body.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise FirmwarePullError(f"SUS lookup for {product_id} did not return JSON") from exc

    update = unwrap_sus_result(document)
    if not update:
        error = unwrap_sus_error(document)
        if error:
            raise FirmwarePullError(f"SUS lookup for {product_id} failed: {error}")
        raise FirmwarePullError(f"SUS lookup for {product_id} did not return a firmware image")

    uri = get_first(update, "URI", "Uri", "uri")
    uri2 = get_first(update, "URI2", "Uri2", "uri2")
    file_name = filename_from_url(uri or uri2 or "")
    if not file_name:
        raise FirmwarePullError(f"SUS lookup for {product_id} did not include a firmware URL")

    return {
        "source": "sus",
        "id": get_first(update, "Id", "ID", "id"),
        "productId": str(get_first(update, "ProductId", "ProductID", "productId") or product_id),
        "file": file_name,
        "size": parse_int(get_first(update, "Size", "size")),
        "sha256": None,
        "uri": uri,
        "uri2": uri2,
        "susRequest": request_body,
        "susResponse": document,
    }


def unwrap_sus_result(document: Any) -> dict[str, Any] | None:
    if isinstance(document, dict):
        responses = document.get("responses")
        if isinstance(responses, list) and responses:
            first = responses[0]
            if isinstance(first, dict) and int(first.get("status", 0)) == 200 and isinstance(first.get("body"), dict):
                return first["body"]
        for key in ("GetLatestImageUpdateResult", "getLatestImageUpdateResult", "GetUpdatesResult", "result"):
            value = document.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value[0]
        if "URI" in document or "uri" in document:
            return document
    if isinstance(document, list) and document and isinstance(document[0], dict):
        return document[0]
    return None


def unwrap_sus_error(document: Any) -> str:
    if not isinstance(document, dict):
        return ""
    responses = document.get("responses")
    if isinstance(responses, list) and responses:
        first = responses[0]
        if isinstance(first, dict) and int(first.get("status", 0)) != 200:
            body = first.get("body")
            if isinstance(body, str):
                return f"status {first.get('status')}: {body}"
            return f"status {first.get('status')}"
    return ""


def get_first(mapping: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return None


def parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return Path(urllib.parse.unquote(parsed.path)).name


def select_update(product_id: str, args: argparse.Namespace) -> dict[str, Any]:
    if args.source == "known":
        return known_update(product_id)
    if args.source == "sus":
        return request_sus_update(product_id, args)

    try:
        return request_sus_update(product_id, args)
    except FirmwarePullError as exc:
        if product_id not in KNOWN_PRODUCTS:
            raise
        print(f"SUS lookup for {product_id} failed, using known table: {exc}", file=sys.stderr)
        return known_update(product_id)


def choose_download_url(update: dict[str, Any], prefer_s3: bool) -> str:
    primary = update.get("uri") or ""
    alternate = update.get("uri2") or ""
    if prefer_s3 and alternate:
        return alternate
    if primary:
        return primary
    if alternate:
        return alternate
    raise FirmwarePullError(f"no download URL for product/skin {update.get('productId')}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file(path: Path, expected_size: int | None, expected_sha256: str | None) -> dict[str, Any]:
    size = path.stat().st_size
    sha256 = sha256_file(path)
    return {
        "path": str(path),
        "size": size,
        "sha256": sha256,
        "sizeOk": expected_size is None or size == expected_size,
        "sha256Ok": expected_sha256 is None or sha256.lower() == expected_sha256.lower(),
    }


def download_file(url: str, path: Path, args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part_path = path.with_name(path.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "harmony-firmware-pull/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            with part_path.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
    except urllib.error.HTTPError as exc:
        if part_path.exists():
            part_path.unlink()
        raise FirmwarePullError(f"download failed for {url}: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        if part_path.exists():
            part_path.unlink()
        raise FirmwarePullError(f"download failed for {url}: {exc.reason}") from exc
    part_path.replace(path)


def inspect_hfw2(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "isZip": False,
        "members": [],
        "intendedSkins": [],
        "images": [],
    }
    if not zipfile.is_zipfile(path):
        return result

    result["isZip"] = True
    with zipfile.ZipFile(path) as archive:
        result["members"] = [info.filename for info in archive.infolist()]
        if "Description.xml" not in result["members"]:
            return result
        description = archive.read("Description.xml")
        root = ElementTree.fromstring(description)
        result["intendedSkins"] = [
            (skin.text or "").strip()
            for skin in root.findall("./INTENDED/SKIN")
            if (skin.text or "").strip()
        ]
        reset_by_name = {
            element.attrib.get("NAME", ""): element.attrib.get("RESET", "")
            for element in root.findall("./ORDER/ORDER_ELEMENT")
        }
        for file_node in root.findall("./FILES/FILE"):
            name = file_node.attrib.get("NAME", "")
            checksum_node = file_node.find("./CHECKSUM")
            checksum = None
            if checksum_node is not None:
                checksum = {
                    "type": checksum_node.attrib.get("TYPE"),
                    "offset": parse_int(checksum_node.attrib.get("OFFSET")),
                    "length": parse_int(checksum_node.attrib.get("LENGTH")),
                    "expected": checksum_node.attrib.get("EXPECTEDVALUE"),
                    "seed": checksum_node.attrib.get("SEED"),
                }
            try:
                member_size = archive.getinfo(name).file_size if name else None
            except KeyError:
                member_size = None
            result["images"].append(
                {
                    "name": name,
                    "bytes": member_size,
                    "remotePath": file_node.attrib.get("PATH"),
                    "operationType": file_node.attrib.get("OPERATIONTYPE"),
                    "version": file_node.attrib.get("VERSION"),
                    "firmwareVersion": file_node.attrib.get("FW_VERSION"),
                    "reset": reset_by_name.get(name, "").lower() == "true",
                    "checksum": checksum,
                }
            )
    return result


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination_root not in (target, *target.parents):
                raise FirmwarePullError(f"refusing to extract {member.filename}: path escapes {destination}")
        archive.extractall(destination)


def maybe_extract(path: Path, inspection: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    if not args.extract:
        return extracted

    outer_dir = path.with_name(f"{path.stem}_hfw2_extracted")
    safe_extract_zip(path, outer_dir)
    extracted["hfw2"] = str(outer_dir)

    if args.extract_payload:
        payloads: list[str] = []
        for image in inspection.get("images", []):
            image_name = image.get("name")
            if not image_name:
                continue
            payload_path = outer_dir / image_name
            if payload_path.exists() and zipfile.is_zipfile(payload_path):
                payload_dir = outer_dir / f"{Path(image_name).stem}_extracted"
                safe_extract_zip(payload_path, payload_dir)
                payloads.append(str(payload_dir))
        extracted["payloads"] = payloads
    return extracted


def product_ids_from_args(args: argparse.Namespace) -> list[str]:
    product_ids: list[str] = []
    if args.all_known:
        product_ids.extend(sorted(KNOWN_PRODUCTS, key=lambda item: int(item)))
    for value in args.products or []:
        product_ids.extend(part.strip() for part in value.split(",") if part.strip())
    seen: set[str] = set()
    unique = []
    for product_id in product_ids:
        if product_id not in seen:
            unique.append(product_id)
            seen.add(product_id)
    return unique


def print_known_table() -> None:
    headers = ("Skin", "Firmware", "File", "What it is", "Codename", "Role")
    rows = [
        (
            product_id,
            entry["firmware"],
            entry["file"],
            entry["product"],
            entry["codename"],
            entry["role"],
        )
        for product_id, entry in sorted(KNOWN_PRODUCTS.items(), key=lambda item: int(item[0]))
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))


def pull_one(product_id: str, args: argparse.Namespace) -> dict[str, Any]:
    update = select_update(product_id, args)
    download_url = choose_download_url(update, args.prefer_s3)
    output_dir = Path(args.output_dir)
    product_dir = output_dir / product_id
    firmware_path = product_dir / update["file"]

    summary: dict[str, Any] = {
        "productId": product_id,
        "source": update["source"],
        "firmware": update.get("id"),
        "file": update["file"],
        "url": download_url,
        "metadataOnly": args.metadata_only,
    }

    if args.metadata_only:
        summary["update"] = update
        return summary

    if firmware_path.exists() and not args.force:
        validation = validate_file(firmware_path, update.get("size"), update.get("sha256"))
        if validation["sizeOk"] and validation["sha256Ok"]:
            print(f"{product_id}: already have {firmware_path}")
        else:
            print(f"{product_id}: existing file does not match known metadata; re-downloading")
            download_file(download_url, firmware_path, args)
    else:
        print(f"{product_id}: downloading {download_url}")
        download_file(download_url, firmware_path, args)

    validation = validate_file(firmware_path, update.get("size"), update.get("sha256"))
    if not validation["sizeOk"]:
        raise FirmwarePullError(
            f"{firmware_path} size mismatch: got {validation['size']}, expected {update.get('size')}"
        )
    if not validation["sha256Ok"]:
        raise FirmwarePullError(
            f"{firmware_path} sha256 mismatch: got {validation['sha256']}, expected {update.get('sha256')}"
        )

    inspection = inspect_hfw2(firmware_path)
    extracted = maybe_extract(firmware_path, inspection, args)

    summary.update(
        {
            "path": str(firmware_path),
            "validation": validation,
            "hfw2": inspection,
            "extracted": extracted,
        }
    )
    manifest = {
        "pull": summary,
        "source": update,
    }
    manifest_path = product_dir / f"{firmware_path.stem}.pull-manifest.json"
    write_json(manifest_path, manifest)
    summary["manifest"] = str(manifest_path)
    if update["source"] == "sus":
        write_json(product_dir / f"{firmware_path.stem}.sus-response.json", update["susResponse"])
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pull Logitech Harmony .hfw2 firmware bundles from SUS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--product", "--skin", action="append", dest="products", help="Product/skin ID; repeat or comma-separate")
    parser.add_argument("--all-known", action="store_true", help="Pull every product/skin in the built-in table")
    parser.add_argument("--list-known", action="store_true", help="Print the built-in product/skin table")
    parser.add_argument("--source", choices=("known", "sus", "auto"), default="known", help="Where to get firmware metadata")
    parser.add_argument("--output-dir", default="firmware_downloads", help="Where firmware files will be written")
    parser.add_argument("--metadata-only", action="store_true", help="Resolve firmware metadata without downloading")
    parser.add_argument("--extract", action="store_true", help="Extract the outer .hfw2 zip after download")
    parser.add_argument("--extract-payload", action="store_true", help="Also extract zip payloads such as ota-update.EzHex")
    parser.add_argument("--prefer-s3", action="store_true", help="Download from the S3 URI instead of CloudFront when available")
    parser.add_argument("--force", action="store_true", help="Re-download even when a matching file already exists")
    parser.add_argument("--json", action="store_true", help="Print the final summary as JSON")
    parser.add_argument("--timeout", type=int, default=60, help="Network timeout in seconds")
    parser.add_argument("--channel", default="production", help="SUS channel for live lookup")
    parser.add_argument("--sys-build", default="0.0.0", help="Reported firmware version for live SUS lookup")
    parser.add_argument("--unit-id", default="", help="Unit ID for live SUS lookup")
    parser.add_argument("--master-unit-id", default="", help="Master unit ID for live SUS lookup")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.extract_payload:
        args.extract = True

    if args.list_known:
        print_known_table()
        if not args.all_known and not args.products:
            return 0

    product_ids = product_ids_from_args(args)
    if not product_ids:
        parser.error("choose --product/--skin, --all-known, or --list-known")

    summaries = []
    for product_id in product_ids:
        summaries.append(pull_one(product_id, args))

    if args.json:
        print(json_dump({"results": summaries}))
    else:
        for item in summaries:
            if item["metadataOnly"]:
                print(f"{item['productId']}: {item['file']} ({item['source']})")
            else:
                validation = item["validation"]
                skins = ", ".join(item.get("hfw2", {}).get("intendedSkins", [])) or "unknown"
                print(f"{item['productId']}: wrote {item['path']}")
                print(f"{item['productId']}: sha256 {validation['sha256']}")
                print(f"{item['productId']}: intended skins {skins}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FirmwarePullError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
