#!/usr/bin/env python3
"""Fail-closed RTVE ingestion and publication for the lottery JSON API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    # GitHub-hosted runners and most Python installations already have a usable
    # CA bundle. The optional dependency makes local Python use the OS trust
    # store as well; TLS verification is never disabled.
    pass


MADRID = ZoneInfo("Europe/Madrid")
ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
USER_AGENT = "NumerosLoteriaNavidad/2026 (+https://github.com/pclemente/NumerosLoteriaNavidad)"
YEAR_PATTERN = re.compile(r"\b20\d{2}\b")


class PipelineError(RuntimeError):
    """A source or candidate failed a publication safety check."""


@dataclass(frozen=True)
class SummaryGroup:
    css_class: str
    keys: tuple[str, ...]
    width: int


@dataclass(frozen=True)
class DrawConfig:
    key: str
    label: str
    year: int
    month: int
    day: int
    source_path: str
    numbers_file: str
    summary_file: str
    status_file: str
    groups: tuple[SummaryGroup, ...]
    minimum_major_prizes: tuple[tuple[str, int], ...]
    expected_total: int

    @property
    def source_root(self) -> str:
        return f"https://www.rtve.es/loterias/{self.source_path}/"

    @property
    def summary_container_id(self) -> str:
        return f"viewLoteria{self.year}"

    @property
    def filenames(self) -> tuple[str, str, str]:
        return self.numbers_file, self.summary_file, self.status_file

    @property
    def summary_keys(self) -> tuple[str, ...]:
        return tuple(key for group in self.groups for key in group.keys)

    @property
    def five_digit_summary_keys(self) -> tuple[str, ...]:
        return tuple(key for group in self.groups if group.width == 5 for key in group.keys)


NAVIDAD = DrawConfig(
    key="navidad",
    label="Lotería de Navidad",
    year=2026,
    month=12,
    day=22,
    source_path="loteria-navidad",
    numbers_file="LoteriaNavidad.json",
    summary_file="LoteriaNavidadResumen.json",
    status_file="LoteriaNavidadStatus.json",
    groups=(
        SummaryGroup("p1", ("numero1",), 5),
        SummaryGroup("p2", ("numero2",), 5),
        SummaryGroup("p3", ("numero3",), 5),
        SummaryGroup("p4", ("numero4", "numero5"), 5),
        SummaryGroup(
            "p5",
            tuple(f"numero{index}" for index in range(6, 14)),
            5,
        ),
    ),
    minimum_major_prizes=(
        ("numero1", 4_000_000),
        ("numero2", 1_250_000),
        ("numero3", 500_000),
        ("numero4", 200_000),
        ("numero5", 200_000),
        ("numero6", 60_000),
        ("numero7", 60_000),
        ("numero8", 60_000),
        ("numero9", 60_000),
        ("numero10", 60_000),
        ("numero11", 60_000),
        ("numero12", 60_000),
        ("numero13", 60_000),
    ),
    expected_total=14_000_000,
)

NINO = DrawConfig(
    key="nino",
    label="Lotería del Niño",
    year=2027,
    month=1,
    day=6,
    source_path="loteria-nino",
    numbers_file="LoteriaElNino.json",
    summary_file="LoteriaElNinoResumen.json",
    status_file="LoteriaElNinoStatus.json",
    groups=(
        SummaryGroup("p1", ("Primer_premio",), 5),
        SummaryGroup("p2", ("Segundo_Premio",), 5),
        SummaryGroup("p3", ("Tercer_Premio",), 5),
        SummaryGroup("p4", ("Extraccion_4_cifras_1", "Extraccion_4_cifras_2"), 4),
        SummaryGroup(
            "p5",
            tuple(f"Extraccion_3_cifras_{index}" for index in range(1, 15)),
            3,
        ),
        SummaryGroup(
            "p6",
            tuple(f"Extraccion_2_cifras_{index}" for index in range(1, 6)),
            2,
        ),
        SummaryGroup("p7", ("Reintegro_1", "Reintegro_2", "Reintegro_3"), 1),
    ),
    minimum_major_prizes=(
        ("Primer_premio", 2_000_000),
        ("Segundo_Premio", 750_000),
        ("Tercer_Premio", 250_000),
    ),
    expected_total=14_000_000,
)

CONFIGS = {config.key: config for config in (NAVIDAD, NINO)}


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise PipelineError(f"{label} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value)
    raise PipelineError(f"{label} must be an integer")


def _title(soup: BeautifulSoup, source: str) -> str:
    if soup.title is None:
        raise PipelineError(f"{source}: missing HTML title")
    return soup.title.get_text(" ", strip=True)


def _require_title_year(
    soup: BeautifulSoup,
    config: DrawConfig,
    source: str,
    *,
    allow_missing: bool = False,
) -> None:
    title = _title(soup, source)
    years = {int(match) for match in YEAR_PATTERN.findall(title)}
    if allow_missing and not years:
        draw_word = "Navidad" if config.key == "navidad" else "Niño"
        if draw_word not in title:
            raise PipelineError(f"{source}: title does not identify {config.label}")
        return
    if years != {config.year}:
        rendered = ", ".join(str(year) for year in sorted(years)) or "none"
        raise PipelineError(
            f"{source}: expected {config.year} in the source title, found {rendered}"
        )


def _number_text(value: str, width: int, label: str) -> int:
    digits = re.sub(r"\D", "", value)
    if not digits:
        raise PipelineError(f"{label}: empty prize number")
    number = int(digits)
    if number < 0 or number >= 10**width:
        raise PipelineError(f"{label}: prize number {number} does not fit {width} digits")
    return number


def parse_summary_html(html: str, config: DrawConfig) -> dict[str, int]:
    """Parse a year-pinned RTVE summary, leaving undrawn prizes at -1."""
    soup = BeautifulSoup(html, "html.parser")
    _require_title_year(soup, config, "summary")
    container = soup.find("ol", id=config.summary_container_id)
    if container is None:
        available = sorted(
            value
            for tag in soup.find_all("ol", id=True)
            if (value := tag.get("id", "")).startswith("viewLoteria")
        )
        raise PipelineError(
            f"summary: missing {config.summary_container_id}; available containers: "
            f"{', '.join(available) or 'none'}"
        )

    summary = {key: -1 for key in config.summary_keys}
    for group in config.groups:
        item = container.find("li", class_=group.css_class)
        if item is None:
            continue
        values = [span.get_text(" ", strip=True) for span in item.find_all("span")]
        populated = [value for value in values if value]
        if len(populated) > len(group.keys):
            raise PipelineError(
                f"summary: {group.css_class} has {len(populated)} values; "
                f"expected at most {len(group.keys)}"
            )
        for key, value in zip(group.keys, populated):
            summary[key] = _number_text(value, group.width, f"summary {key}")
    return summary


def _currency_value(value: str) -> int:
    normalized = value.replace(".", "").replace("€", "").strip()
    if not normalized.isdigit():
        raise PipelineError(f"invalid prize amount {value!r}")
    amount = int(normalized)
    if amount <= 0:
        raise PipelineError(f"prize amount must be positive, got {amount}")
    return amount


def parse_numbers_html(html: str, config: DrawConfig, source: str = "numbers") -> dict[str, str]:
    """Parse one RTVE number-range page after checking its title year."""
    soup = BeautifulSoup(html, "html.parser")
    # RTVE's range-page titles currently omit the draw year. The year is
    # authoritative on the separately fetched summary title/container; a range
    # page that does declare a year must still declare the expected one.
    _require_title_year(soup, config, source, allow_missing=True)
    table = soup.find("table", id="millares")
    if table is None:
        raise PipelineError(f"{source}: missing table#millares")

    prizes: dict[str, str] = {}
    for row in table.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        number_node = row.select_one(".n") if row.get("class") else None
        amount_node = row.select_one(".p") if row.get("class") else None
        if number_node is not None and amount_node is not None:
            # Main-prize rows use one colspan cell (for example 06.703 as
            # ``tr.p1``), so they must be parsed before the ordinary 3-cell
            # rows. This also preserves a leading zero until canonicalization.
            number_text = number_node.get_text(" ", strip=True).replace(".", "")
            amount_text = amount_node.get_text(" ", strip=True)
        elif len(cells) == 3:
            number_text = cells[0].get_text(" ", strip=True).replace(".", "")
            amount_text = cells[2].get_text(" ", strip=True)
        else:
            continue
        if not number_text.isdigit():
            continue
        number = int(number_text)
        if not 0 <= number <= 99_999:
            raise PipelineError(f"{source}: number {number} is outside 00000...99999")
        amount = _currency_value(amount_text)
        key = str(number)
        rendered_amount = str(amount)
        previous = prizes.get(key)
        if previous is not None and previous != rendered_amount:
            raise PipelineError(f"{source}: conflicting amounts for number {number:05d}")
        prizes[key] = rendered_amount
    return prizes


def fetch_text(url: str) -> str:
    if urlparse(url).scheme != "https":
        raise PipelineError(f"refusing non-HTTPS source: {url}")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=(10, 45),
    )
    response.raise_for_status()
    if urlparse(response.url).scheme != "https":
        raise PipelineError(f"source redirected away from HTTPS: {response.url}")
    return response.text


def _numbers_urls(config: DrawConfig) -> list[str]:
    return [
        f"{config.source_root}Loteria_{start:05d}.shtml"
        for start in range(0, 100_000, 5_000)
    ]


def fetch_source(config: DrawConfig) -> tuple[str, list[tuple[str, str]]]:
    summary_html = fetch_text(config.source_root)
    urls = _numbers_urls(config)
    with ThreadPoolExecutor(max_workers=5) as executor:
        pages = list(executor.map(fetch_text, urls))
    return summary_html, list(zip(urls, pages))


def _madrid_now() -> datetime:
    return datetime.now(tz=MADRID)


def _require_draw_started(config: DrawConfig, now: datetime | None = None) -> datetime:
    current = (now or _madrid_now()).astimezone(MADRID)
    if (current.year, current.month, current.day) < (
        config.year,
        config.month,
        config.day,
    ):
        raise PipelineError(
            f"{config.label} {config.year} has not reached its draw date "
            f"({config.day:02d}/{config.month:02d}/{config.year} Europe/Madrid)"
        )
    return current


def build_candidate(
    config: DrawConfig,
    summary_html: str,
    number_pages: Iterable[tuple[str, str]],
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Build and validate an in-memory three-file candidate."""
    observed_at = _require_draw_started(config, now)
    if observed_at.year != config.year:
        raise PipelineError(
            f"candidate timestamp year {observed_at.year} does not match {config.year}"
        )

    parsed_summary = parse_summary_html(summary_html, config)
    drawn_count = sum(value >= 0 for value in parsed_summary.values())
    if drawn_count == 0:
        raise PipelineError("source has no drawn summary prizes; preserving published history")

    prizes: dict[str, str] = {}
    page_count = 0
    for source, html in number_pages:
        page_count += 1
        for number, amount in parse_numbers_html(html, config, source).items():
            previous = prizes.get(number)
            if previous is not None and previous != amount:
                raise PipelineError(f"conflicting amounts for number {int(number):05d}")
            prizes[number] = amount
    if page_count != 20:
        raise PipelineError(f"expected 20 number-range pages, received {page_count}")
    if not prizes:
        raise PipelineError("source has no awarded numbers; preserving published history")

    complete = drawn_count == len(config.summary_keys)
    status = 2 if complete else 1
    # The legacy UIKit controllers decode this complete object as
    # ``[String: String]``, so every value in the numbers payload (including
    # metadata) must remain a JSON string.
    numbers: dict[str, Any] = {"status": str(status), "year": str(config.year)}
    numbers.update({key: prizes[key] for key in sorted(prizes, key=int)})

    summary: dict[str, Any] = {
        "timestamp": int(observed_at.timestamp()),
        "status": status,
        "year": config.year,
    }
    summary.update(parsed_summary)
    if config.key == "navidad":
        summary.update(
            {
                "fraseSorteoPDF": "",
                "fraseListaPDF": "",
                "listaPDF": "",
                "urlAudio": "",
                "error": 0,
            }
        )

    status_payload = {"status": status, "year": config.year, "error": 0}
    candidate = {
        config.numbers_file: numbers,
        config.summary_file: summary,
        config.status_file: status_payload,
    }
    validate_payloads(config, candidate, config.year, require_explicit_year=True)
    return candidate


def _read_payloads(config: DrawConfig, directory: Path) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for filename in config.filenames:
        path = directory / filename
        try:
            with path.open(encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            raise PipelineError(f"cannot read {path}: {error}") from error
        if not isinstance(value, dict):
            raise PipelineError(f"{path}: top-level JSON value must be an object")
        payloads[filename] = value
    return payloads


def _payload_years(
    config: DrawConfig,
    payloads: dict[str, dict[str, Any]],
    require_explicit_year: bool,
) -> set[int]:
    years: set[int] = set()
    for filename, payload in payloads.items():
        if "year" in payload:
            years.add(_integer(payload["year"], f"{filename}.year"))
        elif require_explicit_year:
            raise PipelineError(f"{filename}: missing explicit year")

    summary = payloads[config.summary_file]
    if "timestamp" in summary:
        timestamp = _integer(summary["timestamp"], f"{config.summary_file}.timestamp")
        if timestamp <= 0:
            raise PipelineError(f"{config.summary_file}: timestamp must be positive")
        years.add(datetime.fromtimestamp(timestamp, tz=MADRID).year)
    if not years:
        raise PipelineError("payload set does not declare a source year")
    return years


def _summary_values(config: DrawConfig, summary: dict[str, Any]) -> dict[str, int]:
    values: dict[str, int] = {}
    for group in config.groups:
        for key in group.keys:
            if key not in summary:
                raise PipelineError(f"{config.summary_file}: missing {key}")
            value = _integer(summary[key], f"{config.summary_file}.{key}")
            if value < -1 or value >= 10**group.width:
                raise PipelineError(
                    f"{config.summary_file}.{key}: {value} does not fit {group.width} digits"
                )
            values[key] = value
    return values


def _prizes(config: DrawConfig, numbers: dict[str, Any]) -> dict[str, int]:
    prizes: dict[str, int] = {}
    for key, raw_value in numbers.items():
        if not key.isdigit():
            continue
        number = int(key)
        if not 0 <= number <= 99_999 or key != str(number):
            raise PipelineError(f"{config.numbers_file}: invalid canonical number key {key!r}")
        value = _integer(raw_value, f"{config.numbers_file}.{key}")
        if value <= 0:
            raise PipelineError(f"{config.numbers_file}.{key}: prize must be positive")
        prizes[key] = value
    return prizes


def _validate_summary_coverage(
    config: DrawConfig,
    summary_values: dict[str, int],
    prizes: dict[str, int],
) -> None:
    minimum_prizes = dict(config.minimum_major_prizes)
    for key in config.five_digit_summary_keys:
        number = summary_values[key]
        if number < 0:
            continue
        actual_prize = prizes.get(str(number), 0)
        minimum_prize = minimum_prizes[key]
        if actual_prize < minimum_prize:
            raise PipelineError(
                f"{config.summary_file}.{key}={number:05d} has prize {actual_prize}; "
                f"expected at least {minimum_prize} in {config.numbers_file}"
            )


def validate_payloads(
    config: DrawConfig,
    payloads: dict[str, dict[str, Any]],
    expected_year: int,
    *,
    require_explicit_year: bool,
    strict_final: bool = False,
) -> dict[str, int]:
    """Validate the cross-file API contract and return useful counts."""
    missing = set(config.filenames) - set(payloads)
    if missing:
        raise PipelineError(f"missing payloads: {', '.join(sorted(missing))}")

    years = _payload_years(config, payloads, require_explicit_year)
    if years != {expected_year}:
        rendered = ", ".join(str(year) for year in sorted(years))
        raise PipelineError(f"expected source year {expected_year}, found {rendered}")

    numbers = payloads[config.numbers_file]
    summary = payloads[config.summary_file]
    status_payload = payloads[config.status_file]
    statuses = {
        _integer(numbers.get("status"), f"{config.numbers_file}.status"),
        _integer(summary.get("status"), f"{config.summary_file}.status"),
        _integer(status_payload.get("status"), f"{config.status_file}.status"),
    }
    if len(statuses) != 1:
        raise PipelineError(f"payload statuses disagree: {sorted(statuses)}")
    status = statuses.pop()
    if status not in {0, 1, 2, 3, 4}:
        raise PipelineError(f"unknown lottery status {status}")
    for filename, payload in payloads.items():
        if "error" in payload and _integer(payload["error"], f"{filename}.error") != 0:
            raise PipelineError(f"{filename}: source error is nonzero")

    summary_values = _summary_values(config, summary)
    prizes = _prizes(config, numbers)
    drawn_count = sum(value >= 0 for value in summary_values.values())
    _validate_summary_coverage(config, summary_values, prizes)

    if status == 0:
        if drawn_count or prizes:
            raise PipelineError("status 0 payload contains published prizes")
    else:
        if drawn_count == 0 or not prizes:
            raise PipelineError(f"status {status} payload has no results")
    if status >= 2 and drawn_count != len(summary_values):
        raise PipelineError(f"status {status} summary still has pending prizes")
    if strict_final:
        if status < 2:
            raise PipelineError("final validation requires a completed status")
        _validate_final_coverage(config, summary_values, prizes)

    return {"year": expected_year, "status": status, "summary": drawn_count, "numbers": len(prizes)}


def _validate_final_coverage(
    config: DrawConfig,
    summary_values: dict[str, int],
    prizes: dict[str, int],
) -> None:
    if len(prizes) < 10_000:
        raise PipelineError("final number list has fewer than 10,000 awarded numbers")
    for group in config.groups:
        for key in group.keys:
            value = summary_values[key]
            if value < 0:
                raise PipelineError(f"final summary still has pending {key}")
            suffix = f"{value:0{group.width}d}"
            required = 10 ** (5 - group.width)
            matches = sum(f"{int(number):05d}".endswith(suffix) for number in prizes)
            if matches != required:
                raise PipelineError(
                    f"{key} suffix {suffix} covers {matches} numbers; expected {required}"
                )
    if config.key == "navidad":
        refund = str(summary_values["numero1"])[-1]
        matches = sum(str(int(number))[-1] == refund for number in prizes)
        if matches != 10_000:
            raise PipelineError(
                f"Navidad refund digit {refund} covers {matches} numbers; expected 10000"
            )
    total = sum(prizes.values())
    if total != config.expected_total:
        raise PipelineError(
            f"prize fund is {total}; expected {config.expected_total} before status 4"
        )


def write_payloads(directory: Path, payloads: dict[str, dict[str, Any]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, payload in payloads.items():
        path = directory / filename
        temporary = path.with_name(f".{path.name}.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)


def stage(config: DrawConfig, destination: Path) -> dict[str, int]:
    summary_html, pages = fetch_source(config)
    candidate = build_candidate(config, summary_html, pages)
    write_payloads(destination, candidate)
    return validate_payloads(
        config,
        candidate,
        config.year,
        require_explicit_year=True,
    )


def _semantic_payloads(
    config: DrawConfig, payloads: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    result = json.loads(json.dumps(payloads))
    result[config.summary_file].pop("timestamp", None)
    return result


def _ensure_monotonic(
    config: DrawConfig,
    current: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> None:
    current_status = _integer(current[config.status_file].get("status"), "current status")
    candidate_status = _integer(candidate[config.status_file].get("status"), "candidate status")
    if candidate_status < current_status:
        raise PipelineError(
            f"refusing status downgrade from {current_status} to {candidate_status}"
        )

    current_prizes = _prizes(config, current[config.numbers_file])
    candidate_prizes = _prizes(config, candidate[config.numbers_file])
    for number, amount in current_prizes.items():
        candidate_amount = candidate_prizes.get(number)
        if candidate_amount is None or candidate_amount < amount:
            raise PipelineError(f"candidate retracts or reduces awarded number {int(number):05d}")

    current_summary = _summary_values(config, current[config.summary_file])
    candidate_summary = _summary_values(config, candidate[config.summary_file])
    for key, value in current_summary.items():
        if value >= 0 and candidate_summary[key] != value:
            raise PipelineError(f"candidate retracts or changes summary prize {key}")


def publish(
    config: DrawConfig,
    candidate_dir: Path,
    output_dir: Path,
    confirm_year: int,
    now: datetime | None = None,
) -> bool:
    _require_draw_started(config, now)
    if confirm_year != config.year:
        raise PipelineError(f"confirmation year must be {config.year}")
    candidate = _read_payloads(config, candidate_dir)
    candidate_metadata = validate_payloads(
        config,
        candidate,
        config.year,
        require_explicit_year=True,
    )
    if candidate_metadata["status"] >= 3:
        validate_payloads(
            config,
            candidate,
            config.year,
            require_explicit_year=True,
            strict_final=True,
        )

    if all((output_dir / filename).exists() for filename in config.filenames):
        current = _read_payloads(config, output_dir)
        current_years = _payload_years(config, current, require_explicit_year=False)
        if len(current_years) != 1:
            raise PipelineError(f"current output declares conflicting years: {sorted(current_years)}")
        current_year = next(iter(current_years))
        if current_year > config.year:
            raise PipelineError(
                f"current output year {current_year} is newer than candidate {config.year}"
            )
        if current_year == config.year:
            current_status = _integer(current[config.status_file].get("status"), "current status")
            candidate_status = _integer(
                candidate[config.status_file].get("status"), "candidate status"
            )
            if current_status >= 3 and candidate_status <= 2:
                return False
            _ensure_monotonic(config, current, candidate)
            if _semantic_payloads(config, current) == _semantic_payloads(config, candidate):
                return False

    write_payloads(output_dir, candidate)
    return True


def update(config: DrawConfig, output_dir: Path, confirm_year: int) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"lottery-{config.key}-") as temporary:
        candidate_dir = Path(temporary)
        stage(config, candidate_dir)
        return publish(config, candidate_dir, output_dir, confirm_year)


def inspect(config: DrawConfig, directory: Path) -> dict[str, int]:
    payloads = _read_payloads(config, directory)
    years = _payload_years(config, payloads, require_explicit_year=False)
    if len(years) != 1:
        raise PipelineError(f"published payloads declare conflicting years: {sorted(years)}")
    year = next(iter(years))
    return validate_payloads(
        config,
        payloads,
        year,
        require_explicit_year=False,
    )


def promote(
    config: DrawConfig,
    directory: Path,
    status: int,
    confirm_year: int,
    officially_verified: bool,
) -> None:
    if confirm_year != config.year:
        raise PipelineError(f"confirmation year must be {config.year}")
    if status not in {3, 4}:
        raise PipelineError("promotion status must be 3 or 4")
    if status == 4 and not officially_verified:
        raise PipelineError("status 4 requires --officially-verified")
    payloads = _read_payloads(config, directory)
    metadata = validate_payloads(
        config,
        payloads,
        config.year,
        require_explicit_year=True,
        strict_final=True,
    )
    if status <= metadata["status"]:
        raise PipelineError(f"current status {metadata['status']} is not below {status}")
    payloads[config.numbers_file]["status"] = str(status)
    payloads[config.summary_file]["status"] = status
    payloads[config.status_file]["status"] = status
    validate_payloads(
        config,
        payloads,
        config.year,
        require_explicit_year=True,
        strict_final=True,
    )
    write_payloads(directory, payloads)


def scheduled_draw(now: datetime | None = None) -> DrawConfig | None:
    current = (now or _madrid_now()).astimezone(MADRID)
    for config in CONFIGS.values():
        if (current.year, current.month, current.day) == (
            config.year,
            config.month,
            config.day,
        ):
            return config
    return None


def _metadata_line(metadata: dict[str, int]) -> str:
    return (
        f"year={metadata['year']} status={metadata['status']} "
        f"summary={metadata['summary']} numbers={metadata['numbers']}"
    )


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)

    stage_parser = subcommands.add_parser("stage", help="fetch and write a reviewable candidate")
    stage_parser.add_argument("draw", choices=CONFIGS)
    stage_parser.add_argument("--destination", type=Path, required=True)

    validate_parser = subcommands.add_parser("validate", help="validate a staged candidate")
    validate_parser.add_argument("draw", choices=CONFIGS)
    validate_parser.add_argument("--directory", type=Path, required=True)
    validate_parser.add_argument("--expected-year", type=int, required=True)
    validate_parser.add_argument("--strict-final", action="store_true")

    publish_parser = subcommands.add_parser("publish", help="copy a validated candidate to output")
    publish_parser.add_argument("draw", choices=CONFIGS)
    publish_parser.add_argument("--candidate", type=Path, required=True)
    publish_parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    publish_parser.add_argument("--confirm-year", type=int, required=True)

    update_parser = subcommands.add_parser(
        "update", help="fetch and publish only after the complete candidate validates"
    )
    update_parser.add_argument("draw", choices=CONFIGS)
    update_parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    update_parser.add_argument("--confirm-year", type=int, required=True)

    inspect_parser = subcommands.add_parser("inspect", help="inspect legacy or current published files")
    inspect_parser.add_argument("draw", choices=CONFIGS)
    inspect_parser.add_argument("--directory", type=Path, default=OUTPUT_DIR)

    promote_parser = subcommands.add_parser("promote", help="promote a complete current-year output")
    promote_parser.add_argument("draw", choices=CONFIGS)
    promote_parser.add_argument("--directory", type=Path, default=OUTPUT_DIR)
    promote_parser.add_argument("--status", type=int, required=True)
    promote_parser.add_argument("--confirm-year", type=int, required=True)
    promote_parser.add_argument("--officially-verified", action="store_true")

    subcommands.add_parser(
        "scheduled-draw",
        help="print the configured draw for today's Europe/Madrid date",
    )
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "scheduled-draw":
            config = scheduled_draw()
            if config is not None:
                print(config.key)
            return 0

        config = CONFIGS[args.draw]
        if args.command == "stage":
            metadata = stage(config, args.destination)
            print(f"staged {config.label} candidate: {_metadata_line(metadata)}")
        elif args.command == "validate":
            payloads = _read_payloads(config, args.directory)
            metadata = validate_payloads(
                config,
                payloads,
                args.expected_year,
                require_explicit_year=True,
                strict_final=args.strict_final,
            )
            print(f"valid {config.label} candidate: {_metadata_line(metadata)}")
        elif args.command == "publish":
            changed = publish(config, args.candidate, args.output, args.confirm_year)
            print("published candidate" if changed else "published output already up to date")
        elif args.command == "update":
            changed = update(config, args.output, args.confirm_year)
            print("published source update" if changed else "published output already up to date")
        elif args.command == "inspect":
            metadata = inspect(config, args.directory)
            print(f"valid published {config.label}: {_metadata_line(metadata)}")
        elif args.command == "promote":
            promote(
                config,
                args.directory,
                args.status,
                args.confirm_year,
                args.officially_verified,
            )
            print(f"promoted {config.label} {config.year} to status {args.status}")
        return 0
    except (PipelineError, requests.RequestException) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
