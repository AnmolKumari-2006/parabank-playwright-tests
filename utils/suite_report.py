"""Writes reports/test_suite_report.html after every run: a one-page "Test Suite
Report" in the style of Katalon Studio. Every value comes from the run itself
(results, times, messages, host, OS, browser versions); nothing is typed in by hand.
"""
import html
import platform
import socket
from collections import OrderedDict
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

ORDER = ("failed", "error", "skipped", "passed")          # worst first: decides a test case's status
LABEL = {"passed": "Passed", "failed": "Failed", "error": "Error", "skipped": "Skipped"}
BROWSER = {"chromium": "Chromium", "firefox": "Firefox", "webkit": "WebKit", "": "API (no browser)"}


def _pkg(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "?"


def _ts(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S.") + f"{int(epoch * 10) % 10}"


def _dur(seconds: float) -> str:
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)}m {rest:.3f}s" if minutes else f"{rest:.3f}s"


def _icons(counts: dict) -> str:
    return "".join(f'<span class="cnt"><i class="ic {k}"></i>{counts.get(k, 0)}</span>'
                   for k in ("passed", "failed", "error", "skipped"))


def _badge(status: str) -> str:
    return f'<span class="st"><i class="ic {status}"></i>{LABEL[status]}</span>'


def write_suite_report(rows: list[dict], meta: dict, path: Path) -> Path:
    # one table row per test case; its runs are the browsers it ran on
    cases: "OrderedDict[str, dict]" = OrderedDict()
    for r in sorted(rows, key=lambda r: r["start"]):
        case_id = r["id"].split(" [")[0]
        c = cases.setdefault(case_id, {"path": r["path"], "description": r["description"],
                                       "feature": r["feature"], "kind": r["kind"], "runs": []})
        c["runs"].append(r)
    for c in cases.values():
        outcomes = [r["outcome"] for r in c["runs"]]
        c["status"] = next(s for s in ORDER if s in outcomes) if outcomes else "passed"
        c["counts"] = {k: outcomes.count(k) for k in LABEL}
        c["start"] = min(r["start"] for r in c["runs"])
        c["duration"] = sum(r["duration"] for r in c["runs"])

    totals = {k: sum(1 for c in cases.values() if c["status"] == k) for k in LABEL}
    browsers = " &nbsp;·&nbsp; ".join(
        f"{BROWSER[b]} {html.escape(v)}" for b, v in sorted(meta["browsers"].items())) or "-"

    body_rows = []
    for n, (case_id, c) in enumerate(cases.items(), start=1):
        runs = "".join(
            f"<tr><td>{BROWSER.get(r['browser'], r['browser'])}</td><td>{_badge(r['outcome'])}</td>"
            f"<td>{_ts(r['start'])}</td><td>{r['duration']:.3f}s</td>"
            f"<td class='msg'>{html.escape(r['message']) or '-'}</td></tr>" for r in c["runs"])
        body_rows.append(f"""
<tr class="case" onclick="toggle({n})">
  <td class="arrow" id="a{n}">&#8250;</td><td class="num">{n}</td>
  <td><span class="link">Test Cases/{html.escape(case_id)}</span>
      <div class="sub">{html.escape(c['feature'])} &middot; {html.escape(c['kind'] or '-')} &middot; {html.escape(c['description'])}</div></td>
  <td>{_badge(c['status'])}</td>
  <td class="time">{_ts(c['start']).replace(' ', '<br>', 1)}</td>
  <td>{c['duration']:.3f}s</td><td>{len(c['runs'])}</td><td class="res">{_icons(c['counts'])}</td>
</tr>
<tr class="detail" id="d{n}"><td></td><td colspan="7">
  <div class="path">{html.escape(c['path'])}</div>
  <table class="runs"><tr><th>Browser</th><th>Status</th><th>Start</th><th>Duration</th><th>Message</th></tr>{runs}</table>
</td></tr>""")

    banner = ('<div class="banner">This run tested a ParaBank build with a deliberate bug in its code '
              '(BillPayController: a bill payment is reported as successful but the amount is never taken '
              'from the account). E2E_BIL_01 is expected to fail.</div>' if meta["injected"] else "")
    page = TEMPLATE.format(
        banner=banner,
        host=html.escape(socket.gethostname()), os=html.escape(f"{platform.system()} {platform.release()} {platform.machine()}"),
        platform=html.escape(platform.platform(terse=True)), browsers=browsers,
        base_url=html.escape(meta["base_url"] or "-"),
        tools=f"Playwright {_pkg('playwright')} &nbsp;·&nbsp; pytest {_pkg('pytest')}",
        total=len(cases), passed=totals["passed"], failed=totals["failed"], error=totals["error"],
        skipped=totals["skipped"], runs=len(rows),
        start=_ts(meta["start"]), end=_ts(meta["end"]), duration=_dur(meta["end"] - meta["start"]),
        rows="".join(body_rows))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    return path


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test Suite Report - ParaBank</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,"Segoe UI",Roboto,Arial,sans-serif;font-size:13px;color:#1f2933;background:#fff}}
.top{{padding:12px 18px;border-bottom:1px solid #e3e7ec}}
.top h1{{font-size:15px;margin:0 0 4px}}
.top .crumb{{font-size:11.5px;color:#6b7785}} .top .crumb b{{color:#1f2933;font-weight:600}}
.wrap{{padding:16px 18px 40px}}
.title{{display:flex;align-items:center;gap:12px;margin:8px 0 14px}}
.title h2{{font-size:22px;margin:0;font-weight:600}}
.panel{{border:1px solid #dfe5ec;border-top:4px solid #2b5797;border-radius:6px;background:#f2f5f9;overflow:hidden}}
.env{{display:grid;grid-template-columns:repeat(4,auto 1fr);gap:4px 14px;padding:12px 14px;font-size:12px}}
.env dt{{color:#6b7785}} .env dd{{margin:0;font-weight:500}}
.sum{{display:flex;border-top:1px solid #dfe5ec;background:#eef2f7}}
.counts{{display:flex;align-items:stretch;gap:0;flex:1}}
.box{{padding:10px 18px;text-align:center}} .box b{{display:block;font-size:20px;font-weight:600}}
.box span{{font-size:11.5px;color:#55606d;display:inline-flex;align-items:center;gap:4px}}
.box.total{{background:#fff;border-right:1px solid #dfe5ec;min-width:92px}}
.times{{display:flex;gap:40px;padding:10px 22px;border-left:1px solid #dfe5ec;background:#fff}}
.times div span{{display:block;font-size:11.5px;color:#6b7785}} .times b{{font-weight:500}}
.banner{{margin:12px 0 0;padding:9px 12px;border-radius:6px;background:#fff6d6;border:1px solid #f1d27a;color:#6b4b00}}
table.main{{width:100%;border-collapse:separate;border-spacing:0 6px;margin-top:12px}}
table.main thead th{{background:#2b2b2b;color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:.3px;text-align:left;padding:14px 10px}}
table.main thead th:first-child{{border-radius:6px 0 0 6px}} table.main thead th:last-child{{border-radius:0 6px 6px 0}}
tr.case td{{background:#fff;border-top:1px solid #e3e7ec;border-bottom:1px solid #e3e7ec;padding:10px;vertical-align:middle;cursor:pointer}}
tr.case td:first-child{{border-left:1px solid #e3e7ec;border-radius:6px 0 0 6px}}
tr.case td:last-child{{border-right:1px solid #e3e7ec;border-radius:0 6px 6px 0}}
tr.case:hover td{{background:#f7f9fc}}
.arrow{{width:26px;color:#8a95a3;font-size:18px;transition:transform .15s}} .arrow.open{{transform:rotate(90deg)}}
.num{{width:30px;color:#55606d}}
.link{{color:#3558c9}} .sub{{font-size:11.5px;color:#6b7785;margin-top:3px}}
.time{{color:#55606d;font-size:12px;line-height:1.35;white-space:nowrap}}
.st{{display:inline-flex;align-items:center;gap:5px;white-space:nowrap}}
.res{{white-space:nowrap}} .cnt{{display:inline-flex;align-items:center;gap:4px;margin-right:14px;font-size:12px}}
.ic{{display:inline-block;width:13px;height:13px;border-radius:50%;position:relative;flex:none}}
.ic.passed{{background:#22a447}} .ic.failed{{background:#d92d20}} .ic.error{{background:#b42318}} .ic.skipped{{background:#2f6fde}}
.ic::after{{position:absolute;inset:0;color:#fff;font-size:9px;font-weight:700;display:grid;place-items:center;line-height:13px}}
.ic.passed::after{{content:"\\2713"}} .ic.failed::after{{content:"\\2715"}} .ic.error::after{{content:"!"}} .ic.skipped::after{{content:"\\00BB"}}
tr.detail{{display:none}} tr.detail.open{{display:table-row}}
tr.detail td{{padding:0 10px 10px}}
.path{{font-family:Consolas,monospace;font-size:11.5px;color:#6b7785;margin:2px 0 6px}}
table.runs{{width:100%;border-collapse:collapse;background:#fafbfd;border:1px solid #e3e7ec;border-radius:6px;font-size:12px}}
table.runs th{{text-align:left;color:#55606d;font-weight:600;padding:7px 10px;border-bottom:1px solid #e3e7ec}}
table.runs td{{padding:7px 10px;border-bottom:1px solid #eef1f5;vertical-align:top}}
td.msg{{font-family:Consolas,monospace;font-size:11.5px;color:#7a271a;word-break:break-word}}
.foot{{margin-top:14px;color:#8a95a3;font-size:11.5px}}
</style></head>
<body>
<div class="top"><h1>Test Suite Report</h1>
<div class="crumb">Project: <b>ParaBank</b> - Test Suite ID: <b>tests/ParaBank Test Suite</b></div></div>
<div class="wrap">
<div class="title"><h2>ParaBank Test Suite</h2></div>
<div class="panel">
  <dl class="env">
    <dt>Host name</dt><dd>{host}</dd><dt>Platform</dt><dd>{platform}</dd><dt>Base URL</dt><dd>{base_url}</dd><dt>Tools</dt><dd>{tools}</dd>
    <dt>Local OS</dt><dd>{os}</dd><dt>Browsers</dt><dd>{browsers}</dd><dt>Test runs</dt><dd>{runs}</dd><dt></dt><dd></dd>
  </dl>
  <div class="sum">
    <div class="counts">
      <div class="box total"><b>{total}</b><span>Test Cases</span></div>
      <div class="box"><b>{passed}</b><span><i class="ic passed"></i>Passed</span></div>
      <div class="box"><b>{failed}</b><span><i class="ic failed"></i>Failed</span></div>
      <div class="box"><b>{error}</b><span><i class="ic error"></i>Error</span></div>
      <div class="box"><b>{skipped}</b><span><i class="ic skipped"></i>Skipped</span></div>
    </div>
    <div class="times"><div><span>Start</span><b>{start}</b></div><div><span>End</span><b>{end}</b></div><div><span>Duration</span><b>{duration}</b></div></div>
  </div>
</div>
{banner}
<table class="main"><thead><tr><th></th><th>#</th><th>Test Case</th><th>Status</th><th>Start</th><th>Duration</th><th># Runs</th><th>Result</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="foot">Click a test case to see its result in every browser. "# Runs" = how many times the test case ran (3 browsers; API tests run once).</div>
</div>
<script>
function toggle(n){{document.getElementById('d'+n).classList.toggle('open');document.getElementById('a'+n).classList.toggle('open');}}
</script>
</body></html>
"""