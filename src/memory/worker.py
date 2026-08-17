from queue import Queue
from threading import Thread

from memory.processing import process_conversation
from AI.agent.memory_llm import ollama_memory_llm


class MemoryWorker:
    def __init__(self):
        self._queue = Queue()
        self._worker = Thread(
            target=self._run,
            daemon=True,
        )
        self._worker.start()

    def _run(self):
        while True:
            user_input, assistant_response = self._queue.get()

            try:
                process_conversation(
                    user_input,
                    assistant_response,
                    ollama_memory_llm,
                )
            except Exception as e:
                print(f"⚠️ Memory processing failed: {e}")
            finally:
                self._queue.task_done()

    def submit(
        self,
        user_input: str,
        assistant_response: str,
    ):
        self._queue.put(
            (user_input, assistant_response)
        )


memory_worker = MemoryWorker()