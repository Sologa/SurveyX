import json
import os
import re
import sys
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.client import responses
from pathlib import Path

import matplotlib.pyplot as plt
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

FILE_PATH = Path(__file__).absolute()
BASE_DIR = FILE_PATH.parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))  # run code in any path

from src.configs.config import ADVANCED_CHATAGENT_MODEL, BASE_DIR, CHAT_AGENT_WORKERS
from src.configs.constants import OUTPUT_DIR
from src.configs.logger import get_logger
from src.models.LLM import ChatAgent
from src.models.LLM.utils import load_prompt
from src.models.monitor.time_monitor import TimeMonitor
from src.models.monitor.token_monitor import TokenMonitor
from src.modules.preprocessor.utils import parse_arguments_for_integration_test
from src.modules.utils import clean_chat_agent_format, load_file_as_string, save_result
from src.schemas.base import Base
from src.schemas.outlines import Outlines, SingleOutline

logger = get_logger("src.modules.generator.ContentGenerator")


class ContentGenerator(Base):
    ITER_SPAN = 10

    def __init__(self, task_id: str):
        super().__init__(task_id)
        self.outlines_path = Path(f"{BASE_DIR}/outputs/{task_id}/outlines.json")
        self.work_dir = Path(f"{OUTPUT_DIR}/{str(task_id)}")
        self.paper_dir = self.work_dir / "papers"

    def __process_response(self, reponse: str) -> list[dict] | None:
        res = clean_chat_agent_format(content=reponse)
        try:
            res_dic = json.loads(res)
            assert all(
                "section number" in x and "key information" in x for x in res_dic
            )
            return res_dic
        except Exception as e:
            logger.warning(f"{str(e)}, Failed to process response {reponse[:100]}.")
            return None

    def mount_trees_on_outlines(
        self, trees_path: Path, outlines: Outlines, chat: ChatAgent
    ):
        """Mout each trees to several outlines. Save mount results to paper "mount_outline" field."""

        # read papers
        papers = []
        for file in os.listdir(trees_path):
            if not file.endswith(".json"):
                continue
            paper_path = trees_path / file
            paper_dic = json.loads(load_file_as_string(paper_path))
            if not "attri" in paper_dic:
                continue
            paper_dic["path"] = str(paper_path)
            papers.append(paper_dic)
        # prepare prompts
        prompts_and_index = []
        for i, paper in enumerate(papers):
            prompt = load_prompt(
                f"{BASE_DIR}/resources/LLM/prompts/content_generator/mount_tree_on_outlines.md",
                outlines=str(outlines),
                paper=json.dumps(paper["attri"], indent=4),
            )
            prompts_and_index.append([prompt, i])
        # chat to mount
        retry = 0
        mount_l = [None] * len(papers)
        while prompts_and_index and retry < 3:
            prompts = [x[0] for x in prompts_and_index]
            response_l = chat.safe_batch_remote_chat(
                prompts, desc="mouting trees on outlines..."
            )

            prompts_and_index_copy = []
            for response, (prompt, index) in zip(response_l, prompts_and_index):
                ans = self.__process_response(response)
                if ans:
                    mount_l[index] = ans
                else:
                    prompts_and_index_copy.append([prompt, index])

            retry += 1
            prompts_and_index = prompts_and_index_copy
        # deal chat response
        for mount, paper in zip(mount_l, papers):
            paper["mount_outline"] = mount
            save_result(json.dumps(paper, indent=4), paper["path"])

    def draw_mount_details(self, paper_dir: Path, fig_path: Path) -> None:
        """Draw mount details."""
        section_number_counter = Counter()
        for file in os.listdir(paper_dir):
            paper_path = paper_dir / file
            paper = json.loads(load_file_as_string(paper_path))
            if paper["mount_outline"] is not None:
                section_number_counter.update(
                    mount["section number"] for mount in paper["mount_outline"]
                )

        section_number_counter = sorted(section_number_counter.items())
        x = [snc[0] for snc in section_number_counter]
        y = [snc[1] for snc in section_number_counter]

        plt.figure(figsize=(10, 5))
        plt.bar(x, y)
        for i, value in enumerate(y):
            plt.text(i, value, str(value), ha="center", va="bottom")
        plt.title("mount details")
        plt.xticks(range(len(x)), [k for k in x])
        plt.xlabel("chapter")
        plt.ylabel("count")
        os.makedirs(fig_path.parent, exist_ok=True)
        plt.savefig(fig_path)

    def map_section_to_papers(self, outlines: Outlines, paper_dir: Path) -> dict:
        """Map single outline to a list [keyinfo1, keyinfo2, ...]"""
        sec2info = {  # 用来储存每个section的hint
            subsection.title: []
            for section in outlines.sections
            for subsection in [section] + section.sub
        }

        for file in os.listdir(paper_dir):
            if not file.endswith(".json"):
                continue
            p = paper_dir / file
            dic = json.loads(load_file_as_string(p))
            if not "mount_outline" in dic:
                continue

            try:
                for mount in dic["mount_outline"]:
                    serial_no = mount["section number"]
                    key_info = mount["key information"]
                    single_outline = outlines.serial_no_to_single_outline(serial_no)
                    if single_outline:
                        sec2info[single_outline.title].append(
                            f"bib_name: {dic['bib_name']}\ninfo: {key_info}"
                        )
            except Exception as e:
                tb_str = traceback.format_exc()
                logger.error(f"An error occurred: {e}; The traceback: {tb_str}")
        return sec2info  # sec2info 是一个字典，键为所有outline的title，值为列表，列表中的每个元素是一个hint

    def contains_markdown(
        self, text: str
    ):  # check if a text string contains markdown element.
        markdown_patterns = [
            r"(^|\n)#{1,6} ",  # 标题 (#, ## 等)
            r"(\*\*.*?\*\*|\*.*?\*)",  # 粗体和斜体 (*text* 或 **text**)
            r"(^|\n)[\-\+\*] ",  # 无序列表 (-, +, *)
            r"(^|\n)\d+\.",  # 有序列表 (1. , 2. , etc.)
        ]
        return any(re.search(pattern, text) for pattern in markdown_patterns)

    def write_content_iteratively(
        self,
        papers: list[dict],
        outlines: Outlines,
        written_content: str,
        last_written: str,
        subsection_title: str,
        subsection_desc: str,
        chat: ChatAgent,
    ) -> str:
        res = "**"
        prmpt = load_prompt(
            f"{BASE_DIR}/resources/LLM/prompts/content_generator/fulfill_content_iteratively.md",
            topic=self.topic,
            outlines=str(outlines),
            content=written_content,
            papers="\n\n".join(papers),
            section_title=subsection_title,
            section_desc=subsection_desc,
            last_written=last_written,
        )
        while self.contains_markdown(res) == True:
            tmp = chat.safe_remote_chat(prmpt, model=ADVANCED_CHATAGENT_MODEL)
            if tmp == "no response":
                break
            res = clean_chat_agent_format(content=tmp)
        res = res.replace("\\subsection{Conclusion}", "")
        return res

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def gen_single_section_words(self, section: str, chat: ChatAgent) -> str:
        if "<section_words>" not in section:
            # logger.debug(
            #     "No <section_words> found in the section. No worry, this output is expected, because several sections are not supposed to generate section words.")
            return section

        # chat to generate
        prompt = load_prompt(
            Path(BASE_DIR)
            / "resources"
            / "LLM"
            / "prompts"
            / "content_generator"
            / "write_section_words.md",
            section=section,
        )
        res = chat.safe_remote_chat(prompt)
        try:
            ans = re.findall(r"<answer>(.*?)</answer>", res, re.DOTALL)[0]
            ans = clean_chat_agent_format(ans)
        except:
            logger.error(
                f"Failed to get answer from the chat agent. The response is: {res}"
            )
            logger.error(f"Prompt: {prompt}")
            return section  # keep original section if LLM fails

        # replace the <section_words> with the generated content
        section = section.replace("<section_words>", ans)
        return section

    def gen_section_words(self, mainbody: str, chat: ChatAgent) -> str:
        # split the mainbody into sections
        sections = re.split(r"(?=\\section\{)", mainbody.strip())
        sections = [
            section.strip() for section in sections if section.startswith("\\section{")
        ]
        # add <section_words> to several sections
        add_insert_code = lambda section: re.sub(
            r"(\\section\{[^}]*\})",
            lambda x: f"{x.group(1)}\n<section_words>\n",
            section,
        )
        sections[2:-1] = [add_insert_code(section) for section in sections[2:-1]]
        # generate section words
        logger.info("Start to generate section words.")
        pbar = tqdm(total=len(sections), desc="generating section words...")
        with ThreadPoolExecutor(max_workers=CHAT_AGENT_WORKERS) as executor:
            future_to_index = {
                executor.submit(self.gen_single_section_words, section, chat): idx
                for idx, section in enumerate(sections)
            }
            for future in as_completed(future_to_index):
                result = future.result()
                idx = future_to_index[future]
                sections[idx] = result
                pbar.update(1)
        pbar.close()
        return "\n".join(sections)

    def content_fulfill_iter(
        self,
        paper_dir: str,
        outlines: Outlines,
        chat: ChatAgent,
        mainbody_save_path: str,
    ) -> None:
        sec2info = self.map_section_to_papers(outlines, paper_dir)
        tqdm_bar = tqdm(
            total=sum(len(section.sub) + 1 for section in outlines.sections),
            desc="writing content...",
            position=0,
        )
        written_content = (
            f"\\title{{{outlines.title}}}\n"  # 记录已生成内容，只用来生成prompt
        )
        mainbody = []  # 记录已生成的内容，用来保存到文件

        for i, section in enumerate(outlines.sections):
            out1_title = section.title
            written_content += f"\n\\section{{{out1_title}}}\n"
            mainbody.append(f"\\section{{{out1_title}}}")
            if section.sub == []:
                section.sub.append(SingleOutline(section.title, section.desc))

            for j, subsection in enumerate(section.sub):
                out2_title = subsection.title
                written_content += f"\n\\subsection{{{out2_title}}}\n"

                if not out2_title in sec2info:
                    papers = []
                else:
                    papers = sec2info[out2_title]

                last_written = ""
                with tqdm(
                    total=max(len(papers), 1),
                    desc=f"{i + 1}.{j + 1} {subsection.title[:10]}",
                    position=1,
                    leave=False,
                ) as bar_2:
                    for k in range(0, max(len(papers), 1), self.ITER_SPAN):
                        tmp_papers = papers[k : k + self.ITER_SPAN]
                        res = self.write_content_iteratively(
                            papers=tmp_papers,
                            outlines=outlines,
                            written_content=written_content,
                            last_written=last_written,
                            subsection_title=subsection.title,
                            subsection_desc=subsection.desc,
                            chat=chat,
                        )
                        last_written = res
                        bar_2.update(10)

                mainbody.append(last_written)
                written_content = "\n\n".join(mainbody)
                tqdm_bar.update()

        tqdm_bar.close()
        mainbody = "\n\n".join(mainbody)
        # start to generate section words.
        mainbody = self.gen_section_words(mainbody, chat)
        # save result
        save_result(mainbody, mainbody_save_path)
        logger.info("content fulfill done.")

    def content_fulfill(
        self,
        paper_dir: str,
        outlines: Outlines,
        chat: ChatAgent,
        mainbody_save_path: str,
    ) -> None:
        sec2info = self.map_section_to_papers(outlines, paper_dir)
        tqdm_bar = tqdm(
            total=sum(
                1 if len(section.sub) == 0 else len(section.sub)
                for section in outlines.sections
            ),
            desc="writing content...",
        )
        written_content = f"\\title{{{outlines.title}}}\n"  # 记录已生成内容，生成prompt
        mainbody = []

        for i, section in enumerate(outlines.sections):
            out1_title = section.title
            written_content += f"\n\\section{{{out1_title}}}\n"
            mainbody.append(f"\n\\section{{{out1_title}}}\n")
            if section.sub == []:
                section.sub.append(SingleOutline(section.title, section.desc))

            for j, subsection in enumerate(section.sub):
                out2_title = subsection.title
                written_content += f"\n\\subsection{{{out2_title}}}\n"

                if not out2_title in sec2info:
                    papers = []
                else:
                    papers = sec2info[out2_title]

                res = "**"
                prmpt = load_prompt(
                    f"{BASE_DIR}/resources/LLM/prompts/content_generator/fulfill_content.md",
                    topic=self.topic,
                    outlines=str(outlines),
                    content=written_content,
                    papers="\n\n".join(papers),
                    section_title=subsection.title,
                    section_desc=subsection.desc,
                )
                while self.contains_markdown(res) == True:
                    tmp = chat.safe_remote_chat(prmpt, model=ADVANCED_CHATAGENT_MODEL)
                    if tmp == "no response":
                        break
                    res = clean_chat_agent_format(content=tmp)
                res = res.replace("\\subsection{Conclusion}", "")
                mainbody.append(res)
                written_content = "\n\n".join(mainbody)
                tqdm_bar.update()

        tqdm_bar.close()
        save_result("\n\n".join(mainbody), mainbody_save_path)
        logger.info("Content fulfill done.")

    def gen_abstract(
        self, mainbody_raw_path: str, abstract_save_path: str, chat: ChatAgent
    ):
        mainbody_raw = open(mainbody_raw_path, "r", encoding="utf-8").read()
        prompt = load_prompt(
            f"{BASE_DIR}/resources/LLM/prompts/content_generator/write_abstract.md",
            topic=self.topic,
            mainbody_raw=mainbody_raw,
        )
        logger.debug("Generating abstract.")
        abstract = chat.safe_remote_chat(prompt, model=ADVANCED_CHATAGENT_MODEL)
        abstract = abstract.split("<abstract>")[-1].split("</abstract>")[0].strip()
        abstract = "\n\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n"
        save_result(abstract, abstract_save_path)

    def post_revise(
        self, main_body_raw_path: Path, main_body_save_path: Path, papers_dir: Path
    ):
        """Remove paragraph start with "in essence", "in summary", "in conclusion".
        Remove the illegal citation.
        """
        extract_braced_content = lambda s: (
            m.group(1) if (m := re.search(r"\{(.*?)\}", s)) else None
        )
        main_body_raw = load_file_as_string(main_body_raw_path)
        filter = set(["in conclusion", "in summary", "in essence"])
        legal_cite = [
            json.loads(load_file_as_string(papers_dir / f))["bib_name"]
            for f in os.listdir(papers_dir)
        ]
        main_body = []
        for line in main_body_raw.splitlines(keepends=True):
            # remove paragraphs with "in essence" ...
            if any(e in line.lower() for e in filter):
                continue

            # remove illegal citation
            citations = re.findall(r"\\cite\{(.*?)\}", line)
            for citation in citations:
                if citation not in legal_cite:
                    line = line.replace(f"\\cite{{{citation}}}", "")

            # add "\label{}" to each section and subsection.
            if r"\section" in line:
                section_name = extract_braced_content(line)
                line = line.strip() + f" \\label{{sec:{section_name}}}\n"
            elif r"\subsection" in line:
                section_name = extract_braced_content(line)
                line = line.strip() + f" \\label{{subsec:{section_name}}}\n"

            line = re.sub(
                r"\\textit\{([^}]*)\}",
                lambda m: "\\textit{" + m.group(1).replace("_", "") + "}",
                line,
            )

            main_body.append(line)

        save_result("\n".join(main_body), main_body_save_path)

    def run(self):
        chat_agent = ChatAgent(TokenMonitor(self.task_id, "generate content"))
        time_monitor = TimeMonitor(self.task_id)
        time_monitor.start("generate content")

        # _____ 1. Mount trees on outlines ______________
        outlines = Outlines.from_saved(self.outlines_path)
        self.mount_trees_on_outlines(self.paper_dir, outlines, chat_agent)

        tmp_dir = self.work_dir / "tmp"
        if not tmp_dir.exists():
            tmp_dir.mkdir(exist_ok=True, parents=True)

        # _____ 2. Overview the mount details ___________
        mount_detail_fig_path = tmp_dir / "mount_details.jpg"
        self.draw_mount_details(self.paper_dir, mount_detail_fig_path)

        # _____ 3. Content fulfill _______________________
        main_body_raw_path = tmp_dir / "mainbody.raw.tex"
        self.content_fulfill_iter(
            self.paper_dir, outlines, chat_agent, main_body_raw_path
        )
        # self.content_fulfill(paper_dir, outlines, chat, main_body_raw_path)

        # _____ 4. Generate abstract _____________________
        abstract_save_path = tmp_dir / "abstract.tex"
        self.gen_abstract(main_body_raw_path, abstract_save_path, chat_agent)

        # _____ 5. Post revise ___________________________
        main_body_save_path = tmp_dir / "mainbody.tex"
        self.post_revise(main_body_raw_path, main_body_save_path, self.paper_dir)

        time_monitor.end("generate content")


# python -m src.models.generator.content_generator --task_id <task_id>
if __name__ == "__main__":
    # task_id = parse_arguments_for_integration_test()
    task_id = "2025-02-17-1302_contr"
    chat = ChatAgent()

    content_generator = ContentGenerator(task_id)
    content_generator.run(chat)
