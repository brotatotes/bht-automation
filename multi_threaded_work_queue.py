import threading
import queue
import traceback
import time

class MultiThreadedWorkQueue:
    def __init__(self, num_threads=100, max_retries=1000):
        self.num_threads = num_threads
        self.lock = threading.Lock()
        self.work_queue = queue.Queue()
        self.threads = []
        self.max_retries = max_retries
        self.queue_size = 0

    def do_work(self, func, args):
        retries = 0
        successful = False
        while retries < self.max_retries:
            try:
                func(*args)
                successful = True
                break
            except Exception as e:
                retries += 1
                print(f"❗An error occurred: {e}\n\t{args}")
                # print(traceback.format_exc()) # debugging.
                wait_time = 2 ** retries # exponential backoff.
                print(f"Try # {retries} Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        if not successful:
            print(f"❌ Failed {retries} times. Quitting. ❌\n\t{args}")


    def worker(self):
        while True:
            try:
                func, args = self.work_queue.get(timeout=1)
                self.do_work(func, args)
                self.work_queue.task_done()
                self.queue_size -= 1
                print(f"🚧 COMPLETION: {self.get_progress_string()}")
            except queue.Empty:
                break

    def start(self):
        self.start_time = time.time()
        self.total_tasks = self.queue_size
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.worker)
            self.threads.append(thread)
            thread.start()

    def get_progress_string(self):
        return f"{self.total_tasks - self.queue_size} / {self.total_tasks}"

    def add_task(self, func, args):
        self.work_queue.put((func, args))
        self.queue_size += 1

    def wait_for_completion(self):
        self.work_queue.join()
        self.completion_time = time.time() - self.start_time

    def stop(self):
        for thread in self.threads:
            thread.join()
        print(f"All tasks completed! That took {self.completion_time} seconds.")