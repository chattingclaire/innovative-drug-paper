#!/usr/bin/env python3
"""
政策文件批量下载脚本 v2
- 正文页面：提取文字存 .md
- 附件页面：直接下载 PDF/DOC 链接到政策文件目录
- 失败的：记录链接，你手动在浏览器里打开下载

使用方法：python3 download_policies.py
"""

import os
import time
import re
import requests

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# ========== 任务列表 ==========

# 类型A：用浏览器提取正文
TEXT_TASKS = [
    ("N1", "NMPA-深化审评审批制度改革鼓励创新-2017.md",
     "https://www.gov.cn/zhengce/2017-10/08/content_5230105.htm"),
    ("N5", "NMPA-优化创新药临床试验审评审批试点-2024.md",
     "https://www.gov.cn/zhengce/zhengceku/202408/content_6965736.htm"),
    ("N6", "NMPA-深化药品医疗器械监管改革-2025.md",
     "https://www.gov.cn/zhengce/content/202501/content_6996115.htm"),
    ("H1", "NHSA-36种药品谈判准入通知-2017.md",
     "https://www.mohrss.gov.cn/SYrlzyhshbzb/shehuibaozhang/zcwj/yiliao/201707/t20170718_274153.html"),
    ("C4", "NHC-全面提升医疗质量行动-2023.md",
     "https://www.gov.cn/zhengce/zhengceku/202305/content_6883704.htm"),
    ("G2", "GOV-深化医药卫生体制改革重点任务-2024.md",
     "https://www.gov.cn/zhengce/content/202406/content_6955904.htm"),
    ("H9", "NHSA-目录调整工作方案-2025.md",
     "https://www.gov.cn/zhengce/zhengceku/202507/content_7031575.htm"),
]

# 类型B：用浏览器提取 NMPA 正文（可能有反爬）
NMPA_TEXT_TASKS = [
    ("N7", "NMPA-优化创新药临床试验审评审批公告-2025.md",
     "https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20250912092255131.html"),
    ("N8", "NMPA-药品试验数据保护实施办法-2026.md",
     "https://www.nmpa.gov.cn/directory/web/nmpa/xxgk/ggtg/ypggtg/ypqtggtg/20260515145324185.html"),
    ("N9", "NMPA-药物临床试验质量管理规范GCP-2026.md",
     "https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20260608103856150.html"),
    ("H10", "NHSA-医保药品目录及商保目录-2025.md",
     "https://www.nhsa.gov.cn/art/2025/12/7/art_104_18970.html"),
]

# 类型C：直接下载PDF/DOC附件（用requests直接下载URL）
DOWNLOAD_TASKS = [
    # N3: 突破性治疗等三程序 - 3个DOC附件
    ("N3-1", "NMPA-突破性治疗药物审评工作程序-2020.doc",
     "https://www.nmpa.gov.cn/directory/web/nmpa/images/ufq80tKpxre84La9udzA7b7WMjAyMMTqtdo4MrrFuau45ri9vP4xLmRvYw==.doc"),
    ("N3-2", "NMPA-附条件批准上市工作程序-2020.doc",
     "https://www.nmpa.gov.cn/directory/web/nmpa/images/ufq80tKpxre84La9udzA7b7WMjAyMMTqtdo4MrrFuau45ri9vP4yLmRvYw==.doc"),
    ("N3-3", "NMPA-优先审评审批工作程序-2020.doc",
     "https://www.nmpa.gov.cn/directory/web/nmpa/images/ufq80tKpxre84La9udzA7b7WMjAyMMTqtdo4MrrFuau45ri9vP4zLmRvYw==.doc"),

    # H6: 续约规则 + 竞价规则 PDF
    ("H6-1", "NHSA-谈判药品续约规则-2023.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202307/P020230723620815962734.pdf"),
    ("H6-2", "NHSA-非独家药品竞价规则-2023.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202307/P020230723620816062570.pdf"),

    # H7: 2024年目录调整 4个PDF
    ("H7-1", "NHSA-目录调整工作方案-2024.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202406/P020240629286266591159.pdf"),
    ("H7-2", "NHSA-目录调整申报指南-2024.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202406/P020240629286266776807.pdf"),
    ("H7-3", "NHSA-谈判药品续约规则-2024.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202406/P020240629286266887716.pdf"),
    ("H7-4", "NHSA-非独家药品竞价规则-2024.pdf",
     "https://www.gov.cn/zhengce/zhengceku/202406/P020240629286267066594.pdf"),
]

# 类型D：需要手动下载的（浏览器打开链接让你自己下）
MANUAL_TASKS = [
    ("H11", "NHSA-目录调整工作方案征求意见稿-2026",
     "https://www.nhsa.gov.cn/art/2026/5/9/art_113_20454.html"),
    ("N4", "CDE-抗肿瘤药物临床研发指导原则-2021",
     "在 https://www.cde.org.cn 搜索'第46号通告'"),
]


def clean_text(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()


def extract_text(page):
    """通用正文提取"""
    selectors = [
        '#UCAP-CONTENT', '.pages_content', '.article-content',
        '.TRS_Editor', '#zoom', '.xxgk_con', '.content',
        '.article-con', '.text', 'article', '.Main_article',
    ]
    for sel in selectors:
        try:
            el = page.ele(sel, timeout=2)
            if el and el.text and len(el.text) > 100:
                return el.text
        except:
            pass
    try:
        return page.ele('body').text
    except:
        return ""


def get_title(page):
    for sel in ['h1', '.article-title', '.title', '.pages_title']:
        try:
            el = page.ele(sel, timeout=1)
            if el and el.text and 2 < len(el.text.strip()) < 200:
                return el.text.strip()
        except:
            pass
    return page.title.split('_')[0] if page.title else "未知标题"


def save_md(filepath, title, url, content):
    md = f"# {title}\n\n**来源：** {url}\n\n---\n\n{clean_text(content)}\n"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)


def download_file(url, filepath):
    """用 requests 直接下载文件"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filepath, 'wb') as f:
                f.write(r.content)
            return True
        else:
            return False
    except Exception as e:
        print(f"    requests失败: {e}")
        return False


def main():
    from DrissionPage import ChromiumPage, ChromiumOptions

    print("=" * 60)
    print("  政策文件批量下载脚本 v2")
    print(f"  目录: {SAVE_DIR}")
    print("=" * 60)

    # ===== 第一步：直接下载附件 (不需要浏览器) =====
    print(f"\n📥 第一步：直接下载 PDF/DOC 附件 ({len(DOWNLOAD_TASKS)}个)")
    print("-" * 40)

    dl_ok, dl_fail = 0, []
    for code, filename, url in DOWNLOAD_TASKS:
        filepath = os.path.join(SAVE_DIR, filename)
        if os.path.exists(filepath):
            print(f"  ⏭  {code} 已存在: {filename}")
            dl_ok += 1
            continue

        print(f"  ⬇️  {code} 下载中: {filename}...", end=' ', flush=True)
        if download_file(url, filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"✅ ({size_kb:.0f}KB)")
            dl_ok += 1
        else:
            print(f"❌")
            dl_fail.append((code, filename, url))

    print(f"\n  附件下载完成: 成功{dl_ok}, 失败{len(dl_fail)}")

    # ===== 第二步：浏览器提取正文 =====
    all_text_tasks = TEXT_TASKS + NMPA_TEXT_TASKS
    print(f"\n🌐 第二步：浏览器提取正文 ({len(all_text_tasks)}个)")
    print("-" * 40)

    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--no-first-run')
    co.set_argument('--disable-infobars')

    print("  启动Chrome...")
    page = ChromiumPage(co)

    txt_ok, txt_fail = 0, []
    for code, filename, url in all_text_tasks:
        filepath = os.path.join(SAVE_DIR, filename)
        if os.path.exists(filepath):
            print(f"  ⏭  {code} 已存在: {filename}")
            txt_ok += 1
            continue

        print(f"  🔄 {code} 加载: {url[:55]}...", end=' ', flush=True)
        try:
            page.get(url)
            time.sleep(3)

            content = extract_text(page)
            if content and len(content) > 100:
                title = get_title(page)
                save_md(filepath, title, url, content)
                print(f"✅ {len(content)}字")
                txt_ok += 1
            else:
                print(f"⚠️ 内容过短({len(content)}字)")
                txt_fail.append((code, filename, url))
        except Exception as e:
            print(f"❌ {e}")
            txt_fail.append((code, filename, url))

    # ===== 第三步：手动下载提示 =====
    all_failed = dl_fail + txt_fail + [(c, f, u) for c, f, u in MANUAL_TASKS]
    if all_failed:
        print(f"\n✋ 第三步：以下文件需要手动下载 ({len(all_failed)}个)")
        print("-" * 40)
        for code, filename, url in all_failed:
            print(f"  {code}: {filename}")
            print(f"       {url}")

        print("\n  现在用浏览器依次打开以上链接...")
        for code, filename, url in all_failed:
            if url.startswith('http'):
                try:
                    page.get(url)
                    print(f"\n  已打开 {code}: {url[:50]}...")
                    print(f"  请手动下载/保存，完成后按回车继续")
                    try:
                        input()
                    except EOFError:
                        time.sleep(5)
                except:
                    pass

    # ===== 汇总 =====
    print("\n" + "=" * 60)
    print("  下载汇总")
    print("=" * 60)
    print(f"  附件直接下载: 成功 {dl_ok}/{len(DOWNLOAD_TASKS)}")
    print(f"  正文提取:     成功 {txt_ok}/{len(all_text_tasks)}")
    if all_failed:
        print(f"  需手动处理:   {len(all_failed)}个")
        for code, fn, url in all_failed:
            print(f"    {code} {fn}")
    print("=" * 60)

    try:
        page.quit()
    except:
        pass


if __name__ == '__main__':
    main()
