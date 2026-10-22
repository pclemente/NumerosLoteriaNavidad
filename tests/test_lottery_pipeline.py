import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from lottery_pipeline import (
    MADRID,
    NAVIDAD,
    NINO,
    PipelineError,
    build_candidate,
    parse_numbers_html,
    parse_summary_html,
    publish,
    scheduled_draw,
    validate_payloads,
    write_payloads,
)


def summary_html(config, values):
    groups = []
    for group in config.groups:
        spans = "".join(
            f"<span>{values[key]}</span>"
            for key in group.keys
            if key in values
        )
        groups.append(f'<li class="{group.css_class}">{spans}</li>')
    return (
        f"<html><head><title>{config.label} {config.year}</title></head>"
        f'<body><ol id="{config.summary_container_id}">{"".join(groups)}</ol></body></html>'
    )


def numbers_html(config, prizes):
    rows = "".join(
        f"<tr><td>{number}</td><td>P</td><td>{amount}€</td></tr>"
        for number, amount in prizes.items()
    )
    return (
        f"<html><head><title>{config.label} {config.year}: números premiados</title></head>"
        f'<body><table id="millares"><tr><th>Número</th></tr>{rows}</table></body></html>'
    )


def pages(config, prizes):
    html = numbers_html(config, prizes)
    return [(f"page-{index}", html) for index in range(20)]


def candidate(config, values, prizes, hour=12):
    now = datetime(config.year, config.month, config.day, hour, tzinfo=MADRID)
    return build_candidate(
        config,
        summary_html(config, values),
        pages(config, prizes),
        now=now,
    )


def draw_time(config, hour=12):
    return datetime(config.year, config.month, config.day, hour, tzinfo=MADRID)


def major_prizes(config, values):
    minimums = dict(config.minimum_major_prizes)
    return {str(value): str(minimums[key]) for key, value in values.items()}


class PipelineTests(unittest.TestCase):
    def test_seasons_and_scheduled_dates_are_pinned(self):
        self.assertEqual(NAVIDAD.year, 2026)
        self.assertEqual(NINO.year, 2027)
        self.assertEqual(
            scheduled_draw(datetime(2026, 12, 22, 9, tzinfo=MADRID)),
            NAVIDAD,
        )
        self.assertEqual(
            scheduled_draw(datetime(2027, 1, 6, 12, tzinfo=MADRID)),
            NINO,
        )
        self.assertIsNone(scheduled_draw(datetime(2026, 10, 22, 12, tzinfo=MADRID)))

    def test_wrong_source_year_is_rejected(self):
        html = summary_html(NAVIDAD, {"numero1": 12345}).replace("2026", "2025")
        with self.assertRaisesRegex(PipelineError, "expected 2026"):
            parse_summary_html(html, NAVIDAD)

        numbers = numbers_html(NAVIDAD, {"12345": "4000000"}).replace("2026", "2025")
        with self.assertRaisesRegex(PipelineError, "expected 2026"):
            parse_numbers_html(numbers, NAVIDAD)

    def test_missing_expected_container_is_rejected(self):
        html = summary_html(NAVIDAD, {"numero1": 12345}).replace(
            "viewLoteria2026", "viewLoteria2025"
        )
        with self.assertRaisesRegex(PipelineError, "missing viewLoteria2026"):
            parse_summary_html(html, NAVIDAD)

    def test_special_main_prize_row_preserves_leading_zero_before_canonicalization(self):
        html = (
            "<html><head><title>Lotería del Niño 2027</title></head><body>"
            '<table id="millares"><tr class="p1"><td colspan="3">'
            '<b class="n">06.703</b><br>1er. Premio<br>'
            '<b class="p">2.000.000€</b></td></tr></table></body></html>'
        )
        self.assertEqual(parse_numbers_html(html, NINO), {"6703": "2000000"})

    def test_real_shape_range_title_may_omit_year(self):
        html = numbers_html(NINO, {"6703": "2000000"}).replace(" 2027", "")
        self.assertEqual(parse_numbers_html(html, NINO), {"6703": "2000000"})

    def test_partial_candidate_has_explicit_consistent_year_and_status(self):
        payloads = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"})
        metadata = validate_payloads(
            NAVIDAD,
            payloads,
            2026,
            require_explicit_year=True,
        )
        self.assertEqual(metadata, {"year": 2026, "status": 1, "summary": 1, "numbers": 1})
        self.assertEqual(payloads[NAVIDAD.numbers_file]["year"], "2026")
        self.assertTrue(
            all(isinstance(value, str) for value in payloads[NAVIDAD.numbers_file].values())
        )
        self.assertEqual(payloads[NAVIDAD.summary_file]["year"], 2026)
        self.assertEqual(payloads[NAVIDAD.status_file]["year"], 2026)

    def test_summary_winner_requires_its_minimum_major_prize(self):
        with self.assertRaisesRegex(PipelineError, "expected at least 4000000"):
            candidate(NAVIDAD, {"numero1": 12345}, {"12345": "200"})

    def test_empty_future_results_never_become_a_candidate(self):
        with self.assertRaisesRegex(PipelineError, "no drawn summary prizes"):
            candidate(NAVIDAD, {}, {"12345": "4000000"})

    def test_candidate_is_rejected_before_the_draw_date(self):
        with self.assertRaisesRegex(PipelineError, "has not reached its draw date"):
            build_candidate(
                NAVIDAD,
                summary_html(NAVIDAD, {"numero1": 12345}),
                pages(NAVIDAD, {"12345": "4000000"}),
                now=datetime(2026, 10, 22, 12, tzinfo=MADRID),
            )

    def test_complete_summary_uses_status_two_not_verified_status_four(self):
        values = {key: index for index, key in enumerate(NAVIDAD.summary_keys, start=10001)}
        prizes = major_prizes(NAVIDAD, values)
        payloads = candidate(NAVIDAD, values, prizes)
        self.assertEqual(payloads[NAVIDAD.status_file]["status"], 2)
        self.assertEqual(payloads[NAVIDAD.numbers_file]["status"], "2")

    def test_publish_replaces_prior_year_history_only_with_valid_current_year(self):
        new_payloads = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            output = root / "output"
            write_payloads(staged, new_payloads)

            historical = json.loads(json.dumps(new_payloads))
            for payload in historical.values():
                payload.pop("year", None)
            historical[NAVIDAD.summary_file]["timestamp"] = int(
                datetime(2025, 12, 22, 12, tzinfo=MADRID).timestamp()
            )
            write_payloads(output, historical)

            self.assertTrue(publish(NAVIDAD, staged, output, 2026, now=draw_time(NAVIDAD)))
            published = json.loads((output / NAVIDAD.summary_file).read_text())
            self.assertEqual(published["year"], 2026)

    def test_same_year_results_cannot_retract_a_published_prize(self):
        first = candidate(
            NAVIDAD,
            {"numero1": 12345, "numero2": 54321},
            {"12345": "4000000", "54321": "1250000"},
        )
        regressed = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            output = root / "output"
            write_payloads(output, first)
            write_payloads(staged, regressed)
            with self.assertRaisesRegex(PipelineError, "retracts or reduces"):
                publish(NAVIDAD, staged, output, 2026, now=draw_time(NAVIDAD))

    def test_same_year_accumulated_prize_amount_can_increase(self):
        first = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"})
        increased = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4001000"})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            output = root / "output"
            write_payloads(output, first)
            write_payloads(staged, increased)
            self.assertTrue(
                publish(NAVIDAD, staged, output, 2026, now=draw_time(NAVIDAD))
            )
            numbers = json.loads((output / NAVIDAD.numbers_file).read_text())
            self.assertEqual(numbers["12345"], "4001000")

    def test_unchanged_source_does_not_churn_timestamp(self):
        first = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"}, hour=10)
        later = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"}, hour=11)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            output = root / "output"
            write_payloads(output, first)
            write_payloads(staged, later)
            original = (output / NAVIDAD.summary_file).read_bytes()
            self.assertFalse(
                publish(NAVIDAD, staged, output, 2026, now=draw_time(NAVIDAD))
            )
            self.assertEqual((output / NAVIDAD.summary_file).read_bytes(), original)

    def test_external_status_four_candidate_must_pass_strict_final_validation(self):
        values = {key: index for index, key in enumerate(NAVIDAD.summary_keys, start=10001)}
        prizes = major_prizes(NAVIDAD, values)
        payloads = candidate(NAVIDAD, values, prizes)
        payloads[NAVIDAD.numbers_file]["status"] = "4"
        payloads[NAVIDAD.summary_file]["status"] = 4
        payloads[NAVIDAD.status_file]["status"] = 4
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            write_payloads(staged, payloads)
            with self.assertRaisesRegex(PipelineError, "fewer than 10,000"):
                publish(
                    NAVIDAD,
                    staged,
                    root / "output",
                    2026,
                    now=draw_time(NAVIDAD),
                )

    def test_confirmation_year_is_mandatory(self):
        payloads = candidate(NAVIDAD, {"numero1": 12345}, {"12345": "4000000"})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staged = root / "staged"
            write_payloads(staged, payloads)
            with self.assertRaisesRegex(PipelineError, "confirmation year must be 2026"):
                publish(
                    NAVIDAD,
                    staged,
                    root / "output",
                    2025,
                    now=draw_time(NAVIDAD),
                )


if __name__ == "__main__":
    unittest.main()
