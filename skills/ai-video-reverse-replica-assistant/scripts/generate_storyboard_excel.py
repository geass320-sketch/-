#!/usr/bin/env python3
from __future__ import annotations

import html
import zipfile
from pathlib import Path


def col_name(idx: int) -> str:
    name = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        name = chr(65 + rem) + name
    return name


def xml_escape(text: str) -> str:
    return html.escape(text, quote=False)


def build_sheet_xml(rows: list[list[str]]) -> str:
    body = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{col_name(c_idx)}{r_idx}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(str(value))}</t></is></c>')
        body.append(f"<row r=\"{r_idx}\">{''.join(cells)}</row>")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + ''.join(body) + '</sheetData>'
        '</worksheet>'
    )


def create_xlsx(path: Path) -> None:
    sheets = {
        "角色设定表": [
            ["角色代号", "角色类型", "身份定位", "外貌特征", "服装风格", "性格标签", "角色设定图提示词(EN)", "一致性关键词"],
            ["{角色A}", "主角", "未来城市送件员", "短发、左脸细疤", "机能夹克", "冷静果断", "female courier, short hair, scar on left cheek, tactical jacket, full body, character design sheet, white background, multiple views, cinematic lighting, high quality", "short hair, cheek scar, tactical jacket, calm intense, cinematic"],
        ],
        "完整分镜表": [
            ["镜号", "时间", "时长", "出镜角色", "画面内容", "画面提示词(EN)", "文案/台词", "镜头类型", "功能"],
            ["1", "00:00", "2s", "{角色A}", "雨夜霓虹街道回头观察追兵", "{角色A}, turns back while running, neon rainy alley, medium shot, cinematic lighting", "他们追上来了", "中景", "钩子"],
            ["2", "00:02", "3s", "{角色A}", "冲入狭窄走廊镜头前推", "{角色A}, sprinting into narrow corridor, push-in, film grain", "（喘息声）", "近景", "冲突"],
        ],
        "结构拆解": [["维度", "内容"], ["整体结构", "Hook->Conflict->Climax->Resolution"], ["节奏", "平均2.3s/镜头"]],
        "元提示词模板": [["模板", "{角色} in {场景}, {动作}, {构图}, {光影}, {风格词}, {质量词}"]],
        "验证测试": [["测试项", "输入", "预期"], ["角色替换", "{角色A}=>机械武士", "角色替换但镜头逻辑保持"]],
        "替换指南": [["字段", "策略"], ["角色/场景/动作/风格", "先锁角色一致性，再换场景动作，最后调风格强度"]],
        "JSON结果": [["json"], ['{"analysis_report":{"shots":[]},"generation_package":{}}']],
    }

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets>' + ''.join(
            [f'<sheet name="{xml_escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, name in enumerate(sheets.keys(), start=1)]
        ) + '</sheets></workbook>'
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(
            [f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1)]
        )
        + '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + ''.join(
            [f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets) + 1)]
        )
        + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )

    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="1"><xf xfId="0"/></cellXfs>'
        '</styleSheet>'
    )

    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        zf.writestr('xl/styles.xml', styles)
        for i, (_, rows) in enumerate(sheets.items(), start=1):
            zf.writestr(f'xl/worksheets/sheet{i}.xml', build_sheet_xml(rows))


def create_preview_svg(path: Path) -> None:
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900">
  <rect width="1600" height="900" fill="#ffffff"/>
  <rect x="30" y="20" width="1540" height="70" fill="#1F4E78"/>
  <text x="50" y="65" font-size="34" fill="white" font-family="Arial">Storyboard Excel Preview</text>
  <text x="50" y="130" font-size="24" fill="#1F4E78" font-family="Arial">Sheet: 完整分镜表</text>

  <rect x="50" y="160" width="1500" height="55" fill="#EAF2FB" stroke="#1F4E78"/>
  <text x="60" y="195" font-size="18" fill="#1F4E78" font-family="Arial">镜号 | 时间 | 时长 | 出镜角色 | 画面内容 | 画面提示词(EN) | 文案/台词 | 镜头类型 | 功能</text>

  <rect x="50" y="215" width="1500" height="85" fill="#ffffff" stroke="#CCCCCC"/>
  <text x="60" y="265" font-size="16" fill="#222" font-family="Arial">1 | 00:00 | 2s | {角色A} | 雨夜霓虹街道回头观察追兵 | {角色A}, turns back while running... | 他们追上来了 | 中景 | 钩子</text>

  <rect x="50" y="300" width="1500" height="85" fill="#ffffff" stroke="#CCCCCC"/>
  <text x="60" y="350" font-size="16" fill="#222" font-family="Arial">2 | 00:02 | 3s | {角色A} | 冲入狭窄走廊镜头前推 | {角色A}, sprinting into narrow corridor... | （喘息声） | 近景 | 冲突</text>

  <text x="50" y="450" font-size="22" fill="#1F4E78" font-family="Arial">Included Sheets</text>
  <text x="50" y="490" font-size="18" fill="#222" font-family="Arial">角色设定表 / 完整分镜表 / 结构拆解 / 元提示词模板 / 验证测试 / 替换指南 / JSON结果</text>
</svg>'''
    path.write_text(svg, encoding='utf-8')


def main() -> None:
    assets = Path(__file__).resolve().parent.parent / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    xlsx_path = assets / 'storyboard-example.xlsx'
    svg_path = assets / 'storyboard-example-preview.svg'
    create_xlsx(xlsx_path)
    create_preview_svg(svg_path)
    print(f'Generated: {xlsx_path}')
    print(f'Generated: {svg_path}')


if __name__ == '__main__':
    main()
