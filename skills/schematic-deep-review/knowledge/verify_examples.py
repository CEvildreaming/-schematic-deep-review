#!/usr/bin/env python3
"""Check the synthetic knowledge examples using only the Python standard library.

The checks establish arithmetic and limited internal consistency, not hardware
performance. All generated reports use relative filenames and generic examples.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent


def calculate(name: str, x: dict) -> dict:
    if name == "led_resistor":
        r = (x["supply_V"] - x["led_V"]) / x["target_A"]
        return {"resistance_ohm": r, "power_W": x["target_A"] ** 2 * r}
    if name == "pulls":
        return {"leakage_drop_V": x["leakage_A"] * x["pull_ohm"],
                "low_current_A": x["supply_V"] / x["low_pull_ohm"]}
    if name == "divider":
        top, bottom, load = x["top_ohm"], x["bottom_ohm"], x["load_ohm"]
        loaded_bottom = 1 / (1 / bottom + 1 / load)
        return {"unloaded_V": x["input_V"] * bottom / (top + bottom),
                "divider_A": x["input_V"] / (top + bottom),
                "thevenin_ohm": top * bottom / (top + bottom),
                "loaded_V": x["input_V"] * loaded_bottom / (top + loaded_bottom)}
    if name == "rc":
        tau = x["R_ohm"] * x["C_F"]
        return {"tau_s": tau, "cutoff_Hz": 1 / (2 * math.pi * tau),
                "one_tau_fraction": 1 - math.exp(-1),
                "threshold_time_s": -tau * math.log(1 - x["fraction"])}
    if name == "inductor":
        rms = math.sqrt(x["average_A"] ** 2 + x["ripple_pp_A"] ** 2 / 12)
        return {"peak_A": x["average_A"] + x["ripple_pp_A"] / 2,
                "rms_A": rms, "copper_W": rms ** 2 * x["DCR_ohm"]}
    if name == "lc":
        return {"resonance_Hz": 1 / (2 * math.pi * math.sqrt(x["L_H"] * x["C_F"]))}
    if name == "bead":
        return {"drop_V": x["current_A"] * x["DCR_ohm"],
                "loss_W": x["current_A"] ** 2 * x["DCR_ohm"]}
    if name == "mosfet":
        return {"Vgs_V": x["gate_V"] - x["source_V"],
                "conduction_W": x["current_A"] ** 2 * x["Rds_ohm"],
                "average_gate_A": x["gate_charge_C"] * x["switch_Hz"],
                "ideal_charge_time_s": x["gate_charge_C"] / x["gate_drive_A"]}
    if name == "bjt":
        ib = x["collector_A"] / x["forced_beta"]
        return {"base_A": ib, "base_resistor_ohm": (x["drive_V"] - x["Vbe_V"]) / ib}
    if name == "ldo":
        headroom = x["input_V"] - x["output_V"]
        p1, p2 = headroom * x["load1_A"], headroom * x["load2_A"]
        p_allow = (x["design_limit_C"] - x["ambient_C"]) / x["theta_C_per_W"]
        return {"loss1_W": p1, "loss2_W": p2,
                "rise1_C": p1 * x["theta_C_per_W"],
                "rise2_C": p2 * x["theta_C_per_W"],
                "allowed_W": p_allow, "thermal_current_A": p_allow / headroom}
    if name == "converter_input":
        return {"input_A": x["output_V"] * x["output_A"] / (x["efficiency"] * x["input_V"])}
    if name == "buck":
        duty = x["output_V"] / x["input_V"]
        ripple = (x["input_V"] - x["output_V"]) * duty / (x["L_H"] * x["switch_Hz"])
        return {"duty": duty, "ripple_pp_A": ripple, "peak_A": x["output_A"] + ripple / 2}
    if name == "buck_input_rms":
        return {"rms_A": x["output_A"] * math.sqrt(x["duty"] * (1 - x["duty"]))}
    if name == "transient":
        q = x["deficit_A"] * x["duration_s"]
        esr_drop = x["deficit_A"] * x["ESR_ohm"]
        return {"charge_only_C_F": q / x["droop_V"],
                "ESR_drop_V": esr_drop,
                "ESR_budgeted_C_F": q / (x["droop_V"] - esr_drop),
                "long_pulse_C_F": x["deficit_A"] * x["long_duration_s"] / x["droop_V"],
                "small_cap_time_s": x["small_C_F"] * x["droop_V"] / x["deficit_A"]}
    if name == "crystal":
        return {"equal_leg_C_F": 2 * (x["target_CL_F"] - x["stray_C_F"]),
                "drift_s_per_day": x["error_ppm"] * 1e-6 * x["day_s"]}
    if name == "i2c":
        return {"minimum_pull_ohm": (x["pullup_V"] - x["VOL_V"]) / x["sink_A"],
                "maximum_pull_ohm": x["allowed_rise_s"] / (0.8473 * x["bus_C_F"]),
                "chosen_rise_s": 0.8473 * x["chosen_pull_ohm"] * x["bus_C_F"],
                "chosen_low_A": (x["pullup_V"] - x["VOL_V"]) / x["chosen_pull_ohm"]}
    if name == "adc":
        return {"acquisition_s": (x["bits"] + 1) * math.log(2) * x["total_R_ohm"] * x["sample_C_F"]}
    if name == "opamp":
        ratio = x["feedback_ohm"] / x["input_ohm"]
        ng = 1 + ratio
        return {"noninverting_gain": ng, "noninverting_output_V": ng * x["noninverting_input_V"],
                "inverting_gain": -ratio,
                "inverting_output_V": x["reference_V"] - ratio * (x["inverting_input_V"] - x["reference_V"]),
                "bandwidth_Hz": x["GBW_Hz"] / ng,
                "offset_output_V": ng * x["offset_input_V"],
                "bias_error_V": x["bias_A"] * x["source_ohm"],
                "slew_V_per_s": 2 * math.pi * x["signal_Hz"] * x["output_peak_V"]}
    if name == "integrator":
        slope = -x["input_difference_V"] / (x["input_R_ohm"] * x["feedback_C_F"])
        return {"slope_V_per_s": slope, "change_V": slope * x["duration_s"]}
    raise ValueError(f"Unknown calculation: {name}")


def main() -> int:
    results = []
    generated_links = []

    def record(name, passed, **detail):
        results.append({"check": name, "passed": bool(passed), **detail})

    cases = json.loads((ROOT / "examples.json").read_text(encoding="utf-8"))
    seen = set()
    for case in cases["cases"]:
        record(f"unique-case:{case['id']}", case["id"] not in seen)
        seen.add(case["id"])
        record(f"case-document:{case['id']}", (ROOT / case["document"]).is_file())
        try:
            actual = calculate(case["calculation"], case["inputs_si"])
            record(f"result-keys:{case['id']}", set(actual) == set(case["expected_si"]))
            for key, expected in case["expected_si"].items():
                observed = actual[key]
                record(f"numeric:{case['id']}:{key}",
                       math.isfinite(observed) and math.isclose(observed, expected,
                       rel_tol=case.get("relative_tolerance", 1e-5), abs_tol=1e-15),
                       actual=observed, expected=expected)
        except (KeyError, ValueError, ZeroDivisionError) as error:
            record(f"calculation:{case['id']}", False, error=str(error))

    # Independent cross-checks use KCL, interval integration, and the defining
    # exponential rather than only repeating the printed closed-form answers.
    vd = calculate("divider", {"top_ohm": 30000, "bottom_ohm": 10000,
                               "load_ohm": 100000, "input_V": 5})["loaded_V"]
    record("invariant:loaded-divider-KCL", math.isclose((5-vd)/30000, vd/10000 + vd/100000, rel_tol=1e-12))
    t90 = calculate("rc", {"R_ohm": 10000, "C_F": 1e-7, "fraction": .9})["threshold_time_s"]
    record("invariant:RC-threshold", math.isclose(1-math.exp(-t90/.001), .9, rel_tol=1e-12))
    # Midpoint integration of a two-level input-capacitor current waveform.
    for duty in [.2, .5, .8]:
        n = 10000
        current = [(1-duty if (k+.5)/n < duty else -duty) for k in range(n)]
        rms = math.sqrt(sum(i*i for i in current)/n)
        record(f"invariant:buck-capacitor-zero-mean:{duty}", abs(sum(current)/n) < 1e-12)
        record(f"invariant:buck-capacitor-rms:{duty}", math.isclose(rms, math.sqrt(duty*(1-duty)), rel_tol=1e-10))
    c, current, dt, steps = 500e-6, .25, 200e-6/1000, 1000
    v = 0.0
    for _ in range(steps):
        v += current * dt / c
    record("invariant:transient-charge-integration", math.isclose(v, .1, rel_tol=1e-12))
    t = 13 * math.log(2) * 1e4 * 1e-11
    record("invariant:ADC-half-LSB", math.isclose(math.exp(-t/(1e4*1e-11)), 1/(2**13), rel_tol=1e-12))
    vin, vout, d = 12, 3.3, 3.3/12
    record("invariant:buck-volt-second-balance", abs((vin-vout)*d-vout*(1-d)) < 1e-12)

    # Dimensions are expressed as exponents of (V, A, s).
    def mul(a, b):
        return tuple(x+y for x, y in zip(a, b))
    def div(a, b):
        return tuple(x-y for x, y in zip(a, b))
    def power(a, n):
        return tuple(x*n for x in a)
    volt, amp, second = (1,0,0), (0,1,0), (0,0,1)
    ohm, farad, henry, watt, hz = (1,-1,0), (-1,1,1), (1,-1,1), (1,1,0), (0,0,-1)
    identities = {
        "R*C=time": (mul(ohm,farad), second),
        "I*time/V=capacitance": (div(mul(amp,second),volt), farad),
        "L*di/dt=voltage": (mul(henry,div(amp,second)), volt),
        "I^2*R=power": (mul(power(amp,2),ohm), watt),
        "C*V^2=energy": (mul(farad,power(volt,2)), mul(watt,second)),
        "L*I^2=energy": (mul(henry,power(amp,2)), mul(watt,second)),
        "V/(L*f)=current": (div(volt,mul(henry,hz)), amp),
        "sqrt(L*C)=time": (power(mul(henry,farad),.5), second),
        "C*V/I=time": (div(mul(farad,volt),amp), second),
        "f*V=slew-rate": (mul(hz,volt), div(volt,second)),
    }
    for name, (actual, expected) in identities.items():
        record("dimension:"+name, actual == expected)

    docs = sorted(ROOT.glob("*.md"))
    required_docs = {"index.md", "provenance.md", "passives-and-rc.md", "magnetics.md",
                     "transistor-switches.md", "power-paths-and-transients.md",
                     "mcu-clocks-and-interfaces.md", "operational-amplifiers.md"}
    record("documents:required-topics", {p.name for p in docs} == required_docs)
    for path in docs:
        text = path.read_text(encoding="utf-8")
        record("document:nonempty:"+path.name, len(text.split()) >= 150)
        record("document:no-local-drive-path:"+path.name, not re.search(r"\b[A-Za-z]:[/\\]", text))
        record("document:no-extraction-marker:"+path.name, not any(s in text for s in ["\u200b", "<sub>", "VX:", "wx" + "id_"]))
        for dest in re.findall(r"\]\(([^)]+)\)", text):
            parsed = urlparse(dest)
            if parsed.scheme in {"http", "https"}:
                record("link:official-host:"+path.name+":"+parsed.netloc,
                       parsed.netloc in {"www.ti.com", "www.nxp.com", "www.analog.com"})
            else:
                target = (ROOT / unquote(dest.split("#")[0])).resolve()
                if target == ROOT / "validation.json":
                    generated_links.append(("link:local:"+path.name+":"+dest, target))
                else:
                    record("link:local:"+path.name+":"+dest, target.is_relative_to(ROOT) and target.is_file())
    all_files = [p for p in ROOT.rglob("*") if p.is_file()]
    record("package:text-files-only", all(p.suffix in {".md", ".json", ".py"} for p in all_files))
    record("package:no-source-images-or-PDFs", not any(p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"} for p in all_files))
    report = {
        "scope": "Synthetic arithmetic, dimensional identities, selected independent invariants, local links, and text-only package hygiene. No hardware validation or live URL health check.",
        "case_count": len(cases["cases"]),
        "numeric_result_count": sum(r["check"].startswith("numeric:") for r in results),
        "check_count": len(results),
        "passed_count": sum(r["passed"] for r in results),
        "failed_count": sum(not r["passed"] for r in results),
        "all_passed": all(r["passed"] for r in results),
        "results": results,
    }
    (ROOT / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    # A link to this run's report can only be checked after the report exists.
    for name, target in generated_links:
        record(name, target.is_file())
    report.update(check_count=len(results), passed_count=sum(r["passed"] for r in results),
                  failed_count=sum(not r["passed"] for r in results),
                  all_passed=all(r["passed"] for r in results))
    (ROOT / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    if json.loads((ROOT / "validation.json").read_text(encoding="utf-8")) != report:
        raise RuntimeError("Validation report did not round-trip correctly")
    print(json.dumps({k:v for k,v in report.items() if k != "results"}, indent=2))
    for result in results:
        if not result["passed"]:
            print(json.dumps(result))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
