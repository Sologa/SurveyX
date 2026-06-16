#!/usr/bin/env python3
"""
將 mainbody_post_refined.tex 組裝成完整的 survey.tex

這個腳本重現了 LatexTextBuilder 的功能，展示如何從各個組件組裝成最終的 LaTeX 文檔。
"""

import json
import sys
from pathlib import Path


def load_file_as_string(file_path: Path) -> str:
    """載入檔案內容為字串"""
    return file_path.read_text(encoding='utf-8')


def save_result(content: str, file_path: Path) -> None:
    """儲存內容到檔案"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')


class LatexAssembler:
    """LaTeX 文檔組裝器"""
    
    def __init__(self, template_path: Path):
        """初始化，載入模板"""
        self.tex = load_file_as_string(template_path)
        print(f"✓ 載入模板: {template_path}")
    
    def make_title(self, title: str, author: str = "author"):
        """加入標題、作者、開始文檔"""
        self.tex += f"""\n\\title{{{title}}}\n\\author{{{author}}}\n        
\\begin{{document}}
\\maketitle
"""
        print(f"✓ 加入標題: {title}")
        print(f"✓ 加入作者: {author}")
    
    def make_abstract(self, abstract: str):
        """加入摘要"""
        self.tex += f"\n \n{abstract}\n"
        print(f"✓ 加入摘要 ({len(abstract)} 字元)")
    
    def make_content(self, mainbody: str):
        """加入主體內容"""
        self.tex += "\n" + mainbody
        print(f"✓ 加入主體內容 ({len(mainbody)} 字元)")
    
    def make_reference(self):
        """加入參考文獻區塊"""
        self.tex += """\\newpage
    

\\bibliography{references}
\\bibliographystyle{unsrtnat}

\\vfill"""
        print("✓ 加入參考文獻區塊")
    
    def make_disclaimer(self):
        """加入免責聲明"""
        self.tex += """\\newpage
\\textbf{Disclaimer:}

SurveyX is an AI-powered system designed to automate the generation of surveys. While it aims to produce high-quality, coherent, and comprehensive surveys with accurate citations, the final output is derived from the AI's synthesis of pre-processed materials, which may contain limitations or inaccuracies. As such, the generated content should not be used for academic publication or formal submissions and must be independently reviewed and verified. The developers of SurveyX do not assume responsibility for any errors or consequences arising from the use of the generated surveys.
"""
        print("✓ 加入免責聲明")
    
    def finalize(self):
        """結束文檔"""
        self.tex += "\n \\end{document} \n"
        print("✓ 結束文檔")
    
    def save(self, output_path: Path):
        """儲存最終文檔"""
        save_result(self.tex, output_path)
        print(f"✓ 儲存到: {output_path}")


def main():
    """主函數：組裝 LaTeX 文檔"""
    
    # 設定路徑
    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / "source_files"
    output_dir = base_dir / "compiled_output"
    
    print("=" * 60)
    print("LaTeX 文檔組裝器")
    print("=" * 60)
    print()
    
    # 1. 載入模板
    template_path = source_dir / "survey.ini.tex"
    assembler = LatexAssembler(template_path)
    print()
    
    # 2. 載入 outlines 取得標題
    print("步驟 2: 讀取大綱資訊")
    outlines_path = source_dir / "outlines.json"
    with open(outlines_path, 'r', encoding='utf-8') as f:
        outlines_data = json.load(f)
    title = outlines_data.get("title", "Survey Paper")
    print(f"  標題: {title}")
    print()
    
    # 3. 加入標題和作者
    print("步驟 3: 加入標題與作者")
    author = r"\href{http://www.surveyx.cn}{\textcolor{blue}{\underline{www.surveyx.cn}}}"
    assembler.make_title(title, author)
    print()
    
    # 4. 加入摘要
    print("步驟 4: 加入摘要")
    abstract_path = source_dir / "abstract.tex"
    abstract = load_file_as_string(abstract_path)
    assembler.make_abstract(abstract)
    print()
    
    # 5. 加入主體內容
    print("步驟 5: 加入主體內容 (mainbody_post_refined.tex)")
    mainbody_path = source_dir / "mainbody_post_refined.tex"
    mainbody = load_file_as_string(mainbody_path)
    assembler.make_content(mainbody)
    print()
    
    # 6. 加入參考文獻
    print("步驟 6: 加入參考文獻")
    assembler.make_reference()
    print()
    
    # 7. 加入免責聲明
    print("步驟 7: 加入免責聲明")
    assembler.make_disclaimer()
    print()
    
    # 8. 結束文檔
    print("步驟 8: 結束文檔")
    assembler.finalize()
    print()
    
    # 9. 儲存
    print("步驟 9: 儲存最終文檔")
    output_path = output_dir / "survey.tex"
    assembler.save(output_path)
    print()
    
    print("=" * 60)
    print("✅ 組裝完成！")
    print("=" * 60)
    print(f"\n生成的檔案: {output_path}")
    print(f"檔案大小: {output_path.stat().st_size:,} bytes")
    print("\n下一步: 執行 compile_survey.sh 來編譯 PDF")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 錯誤: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
