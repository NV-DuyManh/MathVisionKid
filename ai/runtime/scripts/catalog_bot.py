"""Visible catalog bot: offline checks, public inventory, optional private aggregate snapshot."""
import argparse
from datetime import datetime, timezone
from html import escape
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_audit import audit_corpus, audit_published
from test_catalog_store import CatalogChecks
from app.tutoring.catalog_store import CatalogStore

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = 'https://github.com/NV-DuyManh/MathVisionKid/actions/workflows/lesson-catalog.yml'


def inspect_catalog(corpus, database=None):
    # Never attach the server's private catalog to a cloud workflow, even by accident.
    if database is not None and os.getenv('GITHUB_ACTIONS') == 'true':
        raise ValueError('Private database inspection is local only')
    report = dict(generatedAt=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                  scope='local' if database is not None else 'public-ci', checks=[],
                  inventory=None, published=None, private=None)
    result = unittest.TextTestRunner(stream=io.StringIO()).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CatalogChecks))
    report['checks'].append(dict(name='Lưu, dùng lại và cách ly catalog',
                                passed=result.wasSuccessful(), tests=result.testsRun))
    if os.getenv('CATALOG_BOT_TEST_STATUS'):
        report['checks'].append(dict(name='Báo cáo, quyền riêng tư và xử lý lỗi của bot',
                                    passed=os.environ['CATALOG_BOT_TEST_STATUS'] == 'success'))
    try:
        report['inventory'] = audit_corpus(corpus)
        report['checks'].append(dict(name='Cấu trúc và trùng đề công khai', passed=True))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        report['checks'].append(dict(name='Cấu trúc và trùng đề công khai', passed=False))
    try:
        report['published']=audit_published(ROOT/'ai/runtime/app/tutoring/data/verified_exercises.json')
        report['checks'].append(dict(name='Catalog dùng chung đã đưa vào Git',passed=True))
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        report['checks'].append(dict(name='Catalog dùng chung đã đưa vào Git',passed=False))
    if database is not None:
        if not database.is_file():
            report['private'] = dict(status='not-created')
        else:
            try:
                audit = CatalogStore(database).audit()
                if any(row['kind'] not in {'plan', 'audio'} for row in audit['groups']):
                    raise ValueError('Unsupported catalog kind')
                # Allowlist aggregates: no owner hashes, sources, paths, plans or audio.
                report['private'] = dict(status='read', expired=audit['expired'], corrupt=audit['corrupt'],
                                         groups=[{key: row[key] for key in ('kind', 'entries', 'bytes', 'hits')}
                                                 for row in audit['groups']])
                report['checks'].append(dict(name='Toàn vẹn kho trên máy chủ', passed=audit['corrupt'] == 0))
            except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
                report['private'] = dict(status='unavailable')
                report['checks'].append(dict(name='Toàn vẹn kho trên máy chủ', passed=False))
    report['passed'] = all(check['passed'] for check in report['checks'])
    return report


def metrics(report):
    shared=[('Đề dùng chung đã phát hành',(report.get('published') or {}).get('exercises','—'))]
    private = report.get('private')
    if private and private['status'] == 'read':
        groups = {row['kind']: row for row in private['groups']}
        return shared+[('Kế hoạch đang lưu', groups.get('plan', {}).get('entries', 0)),
                ('Tệp âm thanh đang lưu', groups.get('audio', {}).get('entries', 0)),
                ('Lượt dùng lại còn ghi nhận', sum(row['hits'] for row in groups.values()))]
    return shared+[('Đề trong bộ kiểm thử công khai', (report.get('inventory') or {}).get('cases', '—')),
            ('Kiểm thử lưu trữ đã chạy', report['checks'][0]['tests']),
            ('Kho học sinh trên máy chủ', 'Không truy cập')]


def markdown(report):
    status = 'Đạt kiểm tra' if report['passed'] else 'Cần kiểm tra lại'
    lines = ['# MathVision Catalog Bot', '', f'**{status}** · {report["generatedAt"]}', '',
             '| Số liệu | Kết quả |', '| :--- | ---: |']
    lines += [f'| {name} | {value} |' for name, value in metrics(report)]
    lines += ['', '| Kiểm tra | Kết quả |', '| :--- | :--- |']
    lines += [f'| {row["name"]} | {"Đạt" if row["passed"] else "Không đạt"} |' for row in report['checks']]
    lines += ['', 'Đây là bản kiểm kê tại thời điểm chạy, không phải màn hình cập nhật trực tiếp.', '',
              'Ứng dụng tự lưu kế hoạch đã kiểm tra sau khi xác nhận đề và âm thanh hợp lệ; '
              'gặp lại đúng đề, đúng tài khoản và cùng phiên bản xử lý thì dùng lại. '
              'Bot GitHub kiểm tra cơ chế đó và bộ dữ liệu công khai; không lấy bài riêng từ máy chủ.', '',
              'Lượt dùng lại chỉ tính trên các bản ghi hiện còn lưu; không phải tổng lịch sử trọn đời. '
              'Kiểm tra cấu trúc/checksum không chứng minh mọi đáp án toán hoặc OCR đều chính xác.', '',
              f'[Mở bot trên GitHub Actions]({WORKFLOW})']
    private = report.get('private')
    if private:
        messages = {'not-created': 'Kho tại đường dẫn được chọn chưa được tạo. Chưa có số liệu để kết luận.',
                    'unavailable': 'Không đọc được kho tại đường dẫn được chọn. Không hiển thị số liệu giả.'}
        if private['status'] in messages:
            lines += ['', messages[private['status']]]
        else:
            lines += ['', f'Bản ghi hết hạn: {private["expired"]}. Sai checksum: {private["corrupt"]}. '
                      'Lần chạy này chỉ đọc; không xóa hoặc sửa kho.']
    return '\n'.join(lines) + '\n'


def dashboard(report):
    good = report['passed']
    cards = ''.join(f'<article><p>{escape(name)}</p><strong>{escape(str(value))}</strong></article>'
                    for name, value in metrics(report))
    rows = ''.join(f'<li><span>{escape(row["name"])}</span><b class="{"good" if row["passed"] else "bad"}">'
                   f'{"Đạt" if row["passed"] else "Không đạt"}</b></li>' for row in report['checks'])
    scope = 'Kho trên máy này · chỉ số tổng hợp' if report['scope'] == 'local' else 'Bộ kiểm thử công khai · GitHub Actions'
    private = report.get('private')
    note = ''
    if private:
        if private['status'] == 'read':
            note = f'Hết hạn: {private["expired"]} · Sai checksum: {private["corrupt"]} · Chỉ đọc, không sửa kho.'
        else:
            note = 'Kho chưa được tạo.' if private['status'] == 'not-created' else 'Không đọc được kho. Chưa có số liệu để kết luận.'
    return f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>MathVision · Catalog Bot</title><style>
:root{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#242044;background:#f6f5fc}}
*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1040px;margin:auto;padding:48px 24px}}
header{{display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap}}
.brand{{font-weight:800;color:#5841b7}}.tag{{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#665b83}}
h1{{font-size:clamp(30px,5vw,46px);letter-spacing:-.04em;line-height:1.1;margin:14px 0}}h2{{font-size:19px;margin:0 0 18px}}
p{{color:#625b75;line-height:1.65}}a{{color:#5841b7}}.button{{display:inline-flex;align-items:center;min-height:46px;padding:12px 18px;border-radius:14px;background:#6545d8;color:white;text-decoration:none;font-weight:650}}
.button:hover{{background:#5033bc}}a:focus-visible{{outline:3px solid #6545d8;outline-offset:4px}}
.hero{{margin:34px 0 24px}}.status{{display:inline-block;border-radius:30px;padding:7px 12px;font-size:13px;font-weight:700;background:{'#e3f3ea' if good else '#fce7e7'};color:{'#206246' if good else '#9c2734'}}}
.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:26px 0}}
article,.panel{{background:white;border:1px solid #e5e0ef;border-radius:20px;padding:24px}}article p{{margin:0 0 12px;font-size:14px}}article strong{{font-size:clamp(25px,4vw,38px);letter-spacing:-.03em}}
.panels{{display:grid;grid-template-columns:1.1fr 1fr;gap:16px}}ul{{list-style:none;padding:0;margin:0}}li{{display:flex;justify-content:space-between;gap:16px;padding:14px 0;border-bottom:1px solid #eeeaf5;font-size:14px}}li:last-child{{border:0}}b{{white-space:nowrap}}.good{{color:#206246}}.bad{{color:#9c2734}}
ol{{padding-left:20px;color:#625b75;line-height:1.8;font-size:14px}}ol li{{display:list-item;padding:3px;border:0}}.note{{font-size:13px;color:#625b75}}footer{{font-size:13px;margin-top:24px;line-height:1.7;color:#625b75}}
@media(max-width:640px){{main{{padding:26px 18px}}.cards,.panels{{grid-template-columns:1fr}}article{{padding:20px}}.hero{{margin-top:26px}}}}
</style></head><body><main><header><div class="brand">MathVision<span style="color:#8c71d6">Kid</span> / Catalog</div>
<a class="button" href="{WORKFLOW}">Mở bot trên GitHub ↗</a></header>
<section class="hero"><div class="tag">{scope}</div><h1>Bài đã giải, sẵn sàng dùng lại.</h1>
<p>Bot kiểm tra kho bài học và âm thanh, để lần học sau không phải tạo lại những gì đã có.</p>
<span class="status">{'Đạt các kiểm tra đã chạy' if good else 'Có kiểm tra chưa đạt'}</span>
<p class="note">Bản chụp lúc {escape(report['generatedAt'])}. Chạy lại bot để cập nhật số liệu.</p></section>
<section class="cards" aria-label="Số liệu catalog">{cards}</section><div class="panels">
<section class="panel"><h2>Kết quả kiểm tra</h2><ul>{rows}</ul><p class="note">{escape(note)}</p></section>
<section class="panel"><h2>Bot làm gì?</h2><ol><li>Ứng dụng lưu kế hoạch đã kiểm tra, sau khi xác nhận đề; lưu âm thanh hợp lệ.</li>
<li>Gặp đúng đề, đúng tài khoản và phiên bản xử lý: dùng lại nội dung đã lưu.</li>
<li>GitHub chạy kiểm tra định kỳ và xuất báo cáo; không thu bài riêng của học sinh.</li></ol></section></div>
<footer>Không có ảnh, nội dung đề, mã tài khoản hay âm thanh học sinh trong báo cáo này.<br>
Lượt dùng lại tính trên các bản ghi còn lưu. Các kiểm tra này không chứng minh mọi đáp án toán hoặc OCR đều chính xác.</footer>
</main></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json')
    parser.add_argument('--database', type=Path, help='Explicit local-only private database; read-only aggregates')
    parser.add_argument('--output', type=Path, default=ROOT/'.local-artifacts/catalog-bot')
    args = parser.parse_args(argv)
    if args.database is not None and os.getenv('GITHUB_ACTIONS') == 'true':
        parser.error('--database is forbidden on GitHub Actions')
    report = inspect_catalog(args.corpus, args.database)
    args.output.mkdir(parents=True, exist_ok=True)
    args.output.joinpath('status.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    args.output.joinpath('summary.md').write_text(markdown(report), encoding='utf-8')
    args.output.joinpath('index.html').write_text(dashboard(report), encoding='utf-8')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(markdown(report))
    print(json.dumps(dict(passed=report['passed'], scope=report['scope'], checks=len(report['checks']))))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
