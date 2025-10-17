import subprocess
import sys
from pathlib import Path

FILE_PATH = Path(__file__).absolute()
BASE_DIR = FILE_PATH.parent.parent
sys.path.insert(0, str(BASE_DIR))  # run code in any path

from src.configs.config import BASE_DIR
from src.configs.logger import get_logger
from src.models.generator import (ContentGenerator, LatexGenerator,
                                  OutlinesGenerator)
from src.models.LLM import ChatAgent
from src.models.post_refine import PostRefiner
from src.modules.preprocessor.data_cleaner import DataCleaner
from src.modules.preprocessor.utils import (create_tmp_config,
                                            parse_arguments_for_offline)

logger = get_logger("tasks.offline_run")


def check_latexmk_installed():
    try:
        # Try running the latexmk command with the --version option
        _ = subprocess.run(['latexmk', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug("latexmk is installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.debug("latexmk is not installed.")
        return False
    except FileNotFoundError:
        logger.debug("latexmk is not installed.")
        return False

def offline_generate(
    task_id: str,
    ref_path: str,
    curated_json: str | None = None,
    skip_llm: bool = False,
    only_clean: bool = False,
):
    chat_agent = ChatAgent()
    
    # preprocess references
    dc = DataCleaner()
    dc.offline_proc(task_id=task_id, ref_path=ref_path, curated_json=curated_json, skip_llm=skip_llm)

    if only_clean:
        logger.info("Only cleaning stage requested; exiting after producing papers and references.bib.")
        return

    # generate outlines
    outline_generator = OutlinesGenerator(task_id)
    outline_generator.run()

    # generate survey
    content_generator = ContentGenerator(task_id=task_id)
    content_generator.run()

    # post refine
    post_refiner = PostRefiner(task_id=task_id, chat_agent=chat_agent)
    post_refiner.run()

    # generate full survey
    latex_generator = LatexGenerator(task_id=task_id)
    latex_generator.generate_full_survey()

    # compile latex
    if check_latexmk_installed():
        logger.info(f"Start compiling with latexmk.")
        latex_generator.compile_single_survey()
    else:
        logger.error(f"Compiling failed, as there is no latexmk installed in this machine.")


if __name__ == "__main__":
    args = parse_arguments_for_offline()
    
    tmp_config = create_tmp_config(args.title, args.key_words)

    topic = tmp_config["topic"]
    task_id = tmp_config["task_id"]
    
    offline_generate(
        task_id=task_id,
        ref_path=args.ref_path,
        curated_json=args.curated_json,
        skip_llm=getattr(args, "skip_llm", False),
        only_clean=getattr(args, "only_clean", False),
    )
