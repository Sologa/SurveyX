"""
@reference:
1.发送本地图片： https://www.cnblogs.com/Vicrooor/p/18227547
"""

import fcntl
import requests
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    RetryError,
)
from tqdm import tqdm
from pathlib import Path

from src.configs.config import (
    REMOTE_URL,
    RESPONSES_URL,
    LOCAL_URL,
    TOKEN,
    BASE_DIR,
    DEFAULT_CHATAGENT_MODEL,
    CHAT_AGENT_WORKERS,
    REASONING_MODELS,
    DEFAULT_REASONING_EFFORT,
)
from src.configs.constants import OUTPUT_DIR

from src.configs.logger import get_logger
from src.models.LLM.utils import encode_image
from src.models.monitor.token_monitor import TokenMonitor

logger = get_logger("src.models.LLM.ChatAgent")
logger.debug(f"ChatAgent pid={os.getpid()}")


class ChatAgent:
    Cost_file = Path(f"{OUTPUT_DIR}/tmp/cost.txt")
    Request_stats_file = Path(f"{OUTPUT_DIR}/tmp/request_stats.txt")
    Record_splitter = "||"
    Record_show_length = 200
    NonRetryToken = "__NON_RETRYABLE__"
    RetryToken = "__RETRYABLE__"

    def __init__(
        self,
        token_monitor: TokenMonitor | None = None,
        token: str = TOKEN,
        remote_url: str = REMOTE_URL,
        local_url: str = LOCAL_URL,
    ) -> None:
        self.remote_url = remote_url
        self.token = token
        self.local_url = local_url
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        self.batch_workers = CHAT_AGENT_WORKERS
        self.token_monitor = token_monitor

    @retry(
        stop=stop_after_attempt(30),
        wait=wait_exponential(min=1, max=300),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def remote_chat(
        self,
        text_content: str,
        image_urls: list[str] = None,
        local_images: list[Path] = None,
        temperature: float = 0.5,
        debug: bool = False,
        model=DEFAULT_CHATAGENT_MODEL,
        reasoning_effort: str | None = None,
    ) -> str:
        """chat with remote LLM, return result.

        If the target model is a reasoning model (configured in REASONING_MODELS),
        the call will be routed to the Responses API and "reasoning.effort" will be
        attached. For non-reasoning models, Chat Completions API is used.
        """
        header = self.header

        # Build messages for Chat Completions compatibility
        messages = [{"role": "user", "content": text_content}]
        # insert image urls ----
        if (
            image_urls is not None
            and isinstance(image_urls, list)
            and len(image_urls) > 0
        ):
            image_url_frame = []
            for url_ in image_urls:
                image_url_frame.append(
                    {"type": "image_url", "image_url": {"url": url_}}
                )
            image_message_frame = {"role": "user", "content": image_url_frame}
            messages.append(image_message_frame)

        # insert local images ----
        if (
            local_images is not None
            and isinstance(local_images, list)
            and len(local_images) > 0
        ):
            local_image_frame = []
            for local_image in local_images:
                local_encoded_image = encode_image(local_image)
                local_image_frame.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{local_encoded_image}"
                        },
                    }
                )
            image_message_frame = {"role": "user", "content": local_image_frame}
            messages.append(image_message_frame)

        # Determine whether to use Responses API (reasoning models)
        is_reasoning_model = False
        # direct match or family prefix match
        if isinstance(model, str):
            is_reasoning_model = model in REASONING_MODELS or any(
                model.startswith(prefix) for prefix in REASONING_MODELS
            )

        if is_reasoning_model:
            # Build Responses API payload
            # Per OpenAI Responses API, content item types must be
            # 'input_text' / 'input_image' (not plain 'text').
            content_items = [
                {"type": "input_text", "text": text_content},
            ]
            # Attach image inputs if provided
            if (
                image_urls is not None
                and isinstance(image_urls, list)
                and len(image_urls) > 0
            ):
                for url_ in image_urls:
                    content_items.append({"type": "input_image", "image_url": url_})
            if (
                local_images is not None
                and isinstance(local_images, list)
                and len(local_images) > 0
            ):
                for local_image in local_images:
                    local_encoded_image = encode_image(local_image)
                    content_items.append(
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{local_encoded_image}",
                        }
                    )

            input_content = [
                {
                    "role": "user",
                    "content": content_items,
                }
            ]
            # Reasoning models must use temperature=1.0
            payload = {
                "model": model,
                "input": input_content,
                "temperature": 1.0,
            }
            # Attach reasoning.effort only for reasoning models
            effort = reasoning_effort or DEFAULT_REASONING_EFFORT
            if effort in {"low", "medium", "high"}:
                payload["reasoning"] = {"effort": effort}
            url = RESPONSES_URL
        else:
            # Default: Chat Completions
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            url = self.remote_url

        response = requests.post(url, headers=header, json=payload)

        if response.status_code != 200:
            logger.error(
                f"chat response code: {response.status_code}\n{response.text[:500]}, retrying..."
            )
            # 记录一次失败请求
            self.update_record(
                status_code=0,
                response_code=response.status_code,
                request=text_content,
                response=response.text,
            )
            # 429 或 5xx 可重试，其餘 4xx 直接 fail-fast
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            else:
                err_msg = None
                try:
                    err_obj = response.json()
                    if isinstance(err_obj, dict):
                        err_msg = err_obj.get("error", {}).get("message")
                except Exception:
                    pass
                raise RuntimeError(
                    f"LLM API error {response.status_code}: "
                    + (err_msg or response.text[:200])
                )
        try:
            res = json.loads(response.text)
            # Parse response for both APIs
            res_text = None
            if isinstance(res, dict):
                # Responses API: prefer unified convenience if present
                if "output_text" in res and isinstance(res["output_text"], str):
                    res_text = res["output_text"]
                # General Responses API: collect text from output items
                elif "output" in res and isinstance(res["output"], list):
                    parts = []
                    for item in res["output"]:
                        if not isinstance(item, dict):
                            continue
                        itype = item.get("type")
                        if itype == "message":
                            # message.content is a list of content parts
                            for c in item.get("content", []) or []:
                                if isinstance(c, dict) and c.get("type") in (
                                    "output_text",
                                    "text",
                                ):
                                    t = c.get("text")
                                    if t:
                                        parts.append(t)
                        elif itype in ("output_text", "text"):
                            t = item.get("text")
                            if t:
                                parts.append(t)
                        elif "text" in item and isinstance(item["text"], str):
                            parts.append(item["text"])
                    if parts:
                        res_text = "\n".join(parts)
                # Chat Completions fallback
                if res_text is None:
                    res_text = (
                        res.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

            # token monitor (support both usage schemas)
            if self.token_monitor and isinstance(res, dict) and "usage" in res:
                usage = res["usage"]
                in_tokens = (
                    usage.get("prompt_tokens")
                    if "prompt_tokens" in usage
                    else usage.get("input_tokens", 0)
                )
                out_tokens = (
                    usage.get("completion_tokens")
                    if "completion_tokens" in usage
                    else usage.get("output_tokens", 0)
                )
                # cached tokens details for prompt/input
                cached_tokens = 0
                try:
                    if "prompt_tokens_details" in usage and isinstance(
                        usage["prompt_tokens_details"], dict
                    ):
                        cached_tokens = int(
                            usage["prompt_tokens_details"].get("cached_tokens", 0)
                        )
                    elif "input_tokens_details" in usage and isinstance(
                        usage["input_tokens_details"], dict
                    ):
                        cached_tokens = int(
                            usage["input_tokens_details"].get("cached_tokens", 0)
                        )
                except Exception:
                    cached_tokens = 0

                self.token_monitor.add_token(
                    model=model,
                    input_tokens=in_tokens or 0,
                    output_tokens=out_tokens or 0,
                    cached_input_tokens=cached_tokens or 0,
                )
        except Exception as e:
            res_text = f"Error: {e}"
            logger.error(f"There is an error: {e}")

        status_code = 0 if response.status_code != 200 else 1
        self.update_record(
            status_code=status_code,
            response_code=response.status_code,
            request=text_content,
            response=res_text,
        )

        if debug:
            return res_text, response
        return res_text

    # --------------- Safe helpers (non-raising) ---------------
    def safe_remote_chat(
        self,
        text_content: str,
        image_urls: list[str] | None = None,
        local_images: list[Path] | None = None,
        temperature: float = 0.5,
        debug: bool = False,
        model=DEFAULT_CHATAGENT_MODEL,
        reasoning_effort: str | None = None,
    ) -> str:
        """Wrapper around remote_chat that never raises.
        Returns "no response" on failure to let callers skip problematic items.
        """
        try:
            return self.remote_chat(
                text_content=text_content,
                image_urls=image_urls,
                local_images=local_images,
                temperature=temperature,
                debug=debug,
                model=model,
                reasoning_effort=reasoning_effort,
            )
        except Exception as e:
            logger.error(f"safe_remote_chat suppressed error: {e}")
            return "no response"

    # map chat index
    def __remote_chat(
        self,
        index,
        content,
        temperature: float = 0.5,
        debug: bool = False,
        model=DEFAULT_CHATAGENT_MODEL,
    ):
        return index, self.remote_chat(
            text_content=content,
            image_urls=None,
            local_images=None,
            temperature=temperature,
            debug=debug,
            model=model,
        )

    def batch_remote_chat(
        self,
        prompt_l: list[str],
        desc: str = "batch_chating...",
        workers: int = CHAT_AGENT_WORKERS,
        temperature: float = 0.5,
    ) -> list[str]:
        """
        开启多线程进行对话
        """
        if workers is None:
            workers = self.batch_workers
        # 创建线程池
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务，并维护 future -> index 映射
            future_l = []
            future_to_index: dict = {}
            for i in range(len(prompt_l)):
                f = executor.submit(self.__remote_chat, i, prompt_l[i], temperature)
                future_l.append(f)
                future_to_index[f] = i
            # 领取任务结果
            res_l = ["no response"] * len(prompt_l)
            for future in tqdm(
                as_completed(future_l),
                desc=desc,
                total=len(future_l),
                dynamic_ncols=True,
            ):
                try:
                    i, resp = future.result()
                    res_l[i] = resp
                except Exception as e:
                    # Classify retryability and record a placeholder result
                    msg = str(e)
                    code = None
                    non_retryable = False
                    try:
                        import re as _re
                        m = _re.search(r"LLM API error (\d+)", msg)
                        if m:
                            code = int(m.group(1))
                    except Exception:
                        code = None

                    # Determine if the error should be treated as non-retryable
                    if code == 400 or (
                        "Invalid prompt" in msg
                        or "limited access" in msg
                        or "safety" in msg
                    ):
                        non_retryable = True
                    else:
                        # Tenacity RetryError likely indicates transient failures after retries
                        non_retryable = False if isinstance(e, RetryError) else False

                    token = self.NonRetryToken if non_retryable else self.RetryToken
                    logger.error(
                        f"batch item failed ({'non-retryable' if non_retryable else 'retryable'}): {msg[:200]}"
                    )
                    # Use the recorded index for this future to place the tagged placeholder
                    i_idx = future_to_index.get(future, None)
                    if isinstance(i_idx, int) and 0 <= i_idx < len(res_l):
                        res_l[i_idx] = f"{token}: {msg}"
        return res_l

    def safe_batch_remote_chat(
        self,
        prompt_l: list[str],
        desc: str = "batch_chating...",
        workers: int = CHAT_AGENT_WORKERS,
        temperature: float = 0.5,
    ) -> list[str]:
        """Batch chat that never raises. Falls back to sequential safe_remote_chat
        if a batch call fails."""
        try:
            return self.batch_remote_chat(
                prompt_l=prompt_l,
                desc=desc,
                workers=workers,
                temperature=temperature,
            )
        except Exception as e:
            logger.error(f"safe_batch_remote_chat falling back due to: {e}")
            results: list[str] = []
            for p in tqdm(prompt_l, desc=f"fallback: {desc}", total=len(prompt_l)):
                results.append(self.safe_remote_chat(p, temperature=temperature))
            return results

    @classmethod
    def update_record(
        cls, status_code: int, response_code: int, request: str, response: str
    ):
        "维护记录文件"
        content = (
            f"{status_code}{cls.Record_splitter}{response_code}{cls.Record_splitter}{request[: cls.Record_show_length]}{cls.Record_splitter}{response[: cls.Record_show_length]}".replace(
                "\n", ""
            )
            + "\n"
        )
        # 检查文件是否存在
        if not os.path.exists(cls.Request_stats_file):
            parent_dir = Path(cls.Request_stats_file).parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            with open(cls.Request_stats_file, "w", encoding="utf-8") as fw:
                fcntl.flock(fw, fcntl.LOCK_EX)  # 加锁
                fw.write(content)
                logger.info(
                    f"record file {cls.Request_stats_file} did not exist, created and initialized with 0.0"
                )
                fcntl.flock(fw, fcntl.LOCK_UN)
        # 更新开销总计
        try:
            with open(cls.Request_stats_file, "a", encoding="utf-8") as fw:
                fcntl.flock(fw, fcntl.LOCK_EX)
                fw.write(content)
                fcntl.flock(fw, fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Failed to update cost: {e}")

    def local_chat(self, query, debug=False) -> str:
        """
        调用本地LLM进行推理, 保证端口已开启
        """
        query = """
            <|begin_of_text|><|start_header_id|>system<|end_header_id|>
            You are a helpful AI assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>
            {}<|eot_id|><|start_header_id|>assistant<|end_header_id|>""".format(query)

        payload = json.dumps(
            {
                "prompt": query,
                "temperature": 1.0,
                "max_tokens": 102400,
                "n": 1,
                # 可选的参数在这里：https://github.com/vllm-project/vllm/blob/main/vllm/sampling_params.py
            }
        )
        headers = {"Content-Type": "application/json"}
        res = requests.request("POST", self.local_url, headers=headers, data=payload)
        if res.status_code != 200:
            logger.info("chat response code: {}".format(res.status_code), query[:20])
            return "chat response code: {}".format(res.status_code)
        if debug:
            return res
        return res.json()["text"][0].replace(query, "")

    def __local_chat(self, index, query):
        return index, self.local_chat(query, debug=True)

    def batch_local_chat(self, query_l, worker=16, desc="bach local inferencing..."):
        """
        多线程本地推理
        """
        with ThreadPoolExecutor(max_workers=worker) as executor:
            # 提交任务
            future_l = [
                executor.submit(self.__local_chat, i, query_l[i])
                for i in range(len(query_l))
            ]
            # 领取任务结果
            res_l = ["no response"] * len(query_l)
            for future in tqdm(as_completed(future_l), desc=desc, total=len(future_l)):
                i, resp = future.result()
                res_l[i] = resp
        return res_l

    @staticmethod
    def show_request_stats():
        stats_file = ChatAgent.Request_stats_file
        logger.info(f"stats_file: {stats_file}")

        with stats_file.open("r", encoding="utf-8") as fr:
            succ_count = 0
            total_count = 0
            for line in fr:
                elements = line.strip().split(ChatAgent.Record_splitter)
                succ_count += int(elements[0])
                total_count += 1
            logger.info(f"请求成功率：{round(succ_count / total_count * 100, 2)}%")

    @staticmethod
    def clean_request_stats():
        stats_file = ChatAgent.Request_stats_file
        if stats_file.exists():
            logger.info(f"remove {stats_file}.")


if __name__ == "__main__":
    agent = ChatAgent()
    text_content = "图片里面有什么"

    # result = agent.remote_chat(text_content="今天天气怎么样",  model="gpt-4o")
    # print(result)
    #
    # image_urls = ["https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"]
    # result = agent.remote_chat( text_content=text_content, image_urls=image_urls, temperature=0.5, model="gpt-4o")
    # print(result)

    local_images = [f"{BASE_DIR}/resources/dummy_data/figs/dog_and_girl.jpeg"]
    result = agent.remote_chat(
        text_content=text_content,
        local_images=local_images,
        temperature=0.5,
        model="gpt-4o",
    )
    print(result)

    ChatAgent.show_request_stats()
