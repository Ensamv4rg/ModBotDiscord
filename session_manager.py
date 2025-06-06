from database import Active
import threading
import requests
from urllib.parse import quote
import time
import random
class Session_Manager:
    VALID_MODES = {"unique"}

    def __init__(self, mode="unique"):
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.sessions = {}

    def add_session(self, server_id):
        if server_id in self.sessions:
            raise ValueError(f"Session for server_id {server_id} already exists")
        if self.mode == "unique":
            self.sessions[server_id] = (AIUnique(), DBUnique(server_id))
        else:
            raise ValueError("Shared mode not supported")
    
    def remove_session(self, server_id):
        if server_id not in self.sessions:
            raise ValueError(f"No session for server_id {server_id}")
        self.sessions[server_id][1].close_pool()
        del self.sessions[server_id]

    def restart_session(self, server_id):
        if server_id not in self.sessions:
            raise ValueError(f"No session for server_id {server_id}")
        self.remove_session(server_id)
        self.add_session(server_id)
    
    def __str__(self, verbose=False):
        n_of_sess = len(self.sessions)
        if not verbose:
            return f"{n_of_sess} sessions open\nRunning in Mode: {self.mode}"
        else:
            details = "\n".join([f"Server ID: {key}" for key in self.sessions.keys()])
            return f"{n_of_sess} sessions opened! Details below\n{details}"

class Process:
    def __init__(self, thread_number):
        self.max_thread_number = thread_number
        self.active_thread_count = 0
        self.priority_levels = ['high_task', 'med_task', 'low_task']
        self.high_task = []
        self.med_task = []
        self.low_task = []
        self.active_thread_count_lock = threading.Lock()

        self.__high_task_lock = threading.Lock()
        self.__med_task_lock = threading.Lock()
        self.__low_task_lock = threading.Lock()

        self.__priority_locks = {
            'high_task': self.__high_task_lock,
            'med_task': self.__med_task_lock,
            'low_task': self.__low_task_lock
        }

        self.tasks = {}
        
        self.results = {}
        self.results_lock = threading.Lock()

    def _check_free(self):
        with self.active_thread_count_lock:
            return self.active_thread_count < self.max_thread_number

    def create_thread(self,task,priority="low_task"):
        

        if priority not in self.priority_levels:
            raise ValueError(f"Invalid priority: {priority}")
        if not isinstance(task, tuple) or len(task) != 2:
            raise ValueError("Task must be a tuple (task_name, arguments)")
        
        task_name,task_args = task

        if task_name not in self.tasks:
            raise ValueError(f"Unknown task: {task_name}")
        
        with self.active_thread_count_lock:
            if self.active_thread_count >= self.max_thread_number:
                with self.__priority_locks[priority]:
                    getattr(self, priority).append(task)
                return
            self.active_thread_count += 1
        
        
        t = threading.Thread(target=self.tasks[task_name],args=task_args)
        with self.results_lock:
            self.results[task_args[-1]] = "unfinished"
        t.start()
                
        

    def clean(self):
        with self.active_thread_count_lock: #Reduces active thread count. Does this before restarting new thread to avoid double counting
            self.active_thread_count-=1
            
        for c in self.priority_levels:
            priority =c
            with self.__priority_locks[priority]:
                c = getattr(self,c)
                if len(c) > 0:
                    task = c.pop(0)
                    self.create_thread(task,priority)
                    return

        return 

    

class AIUnique(Process):
    def __init__(self):
        super().__init__(3)
        methods = ['entry_point','clear_server_history']
        self.tasks = {method: getattr(self, method) for method in methods}
        self.public_url = 'https://4607-34-83-245-125.ngrok-free.app'

    def clear_server_history(self,server_id,task_id):
        url = f"{self.public_url}/clearHistory?server_id={quote(str(server_id))}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            response = response.text
        except Exception as e:
            print(f"Error connecting to AI server. Error: {e}")
            response = "Couldn't clear server history. AI module unreachable."

        with self.results_lock:
            self.results[task_id] = response
            return
        

    def entry_point(self, server_id, username, input,task_id=None):
        try:
            url = f"{self.public_url}/determine?server_id={quote(str(server_id))}&username={quote(username)}&sentence={quote(input)}"

            try:
                response = requests.get(url)
                response.raise_for_status()
                response = response.text
                
            except Exception as e:
                print(f"Error connecting to AI Module: {e}")
                response =  f"AI Model offline for now. Can't process user {username}'s query:\n '{input}'\n right now."

            if task_id:
                with self.results_lock:
                    self.results[task_id] = response
                return 
            return response
            
        except Exception as e:
            return f"Error: {e}"
        finally:
            self.clean()

class DBUnique(Process):
    def __init__(self, server_id):
        super().__init__(10)
        self.db = Active(server_id)
        methods = ['add_server', 'add_server_role_id', 'add_topic_for_server', 'remove_server', 'remove_topic_from_server', 'return_topics_for_server', 'add_session', 'deactivate_session']
        self.tasks = {method: getattr(self, method) for method in methods}

    def close_pool(self):
        self.db.close()

    def add_server(self, role_id):
        pass

    def add_server_role_id(self, role_id):
        pass

    def add_topic_for_server(self, topic_id):
        pass

    def remove_server(self):
        pass

    def remove_topic_from_server(self, topic_id):
        pass

    def return_topics_for_server(self, ids=False):
        pass

    def add_session(self):
        pass

    def deactivate_session(self):
        pass
#The 'active' class does not currently support global servers. This really only affects DB operations. But for consistency purposes, AI operations would be placed on hold for now.
"""
class ProcessX(): #Process class for global process. This class would be used assuming there are only 2 Processes all servers share.
    def __init__(self):
        self.priority_levels = ['high_task','med_task','low_task']
        self.max_thread_number = {} #The session ID(server ID) is the key, and the number of threads allowed is the value
        self.active_thread_count = {} #Session ID key, value = number of active threads
        
        self.high_task={} #Key would be the server ID, value would be a list of threads.
        self.med_task={}
        self.low_task={}

        self.active_thread_count_lock = {} #Server ID as key, lock as value
        self.__queue_lock = {} #Server ID as key, lock as value

        self.tasks = {}#Available functions. Name as their Key, value as the function

    def add_server(self,server_id,max_thread=3):
        self.max_thread_number[server_id] = max_thread
        self.active_thread_count[server_id] = 0
        self.active_thread_count_lock[server_id] = threading.Lock()
        self.__queue_lock[server_id] = threading.Lock()
        self.high_task[server_id] = []
        self.med_task[server_id] = []
        self.low_task[server_id] = []

    def remove_server(self,server_id):
        del self.max_thread_number[server_id]
        del self.active_thread_count[server_id]
        del self.active_thread_count_lock[server_id]
        del self.__queue_lock[server_id]
        del self.high_task[server_id]
        del self.med_task[server_id]
        del self.low_task[server_id]
    
    def _check_free(self,server_id):
       \"""Function to see if a thread is free""\"
        with self.active_thread_count_lock[server_id]:
            if self.active_thread_count[server_id] >= self.max_thread_number[server_id]:
                return False
        return True
    
    def create_thread(self,server_id,task,priority="low_task"):
        "\""Function to add threads to queue and initiatilaize thread startup""\"
        with self.__queue_lock[server_id]:
            if not self._check_free(server_id):
                priority = getattr(self,priority)
                priority[server_id].append(task)
                return
        
        t = threading.Thread(target=self.tasks[task],args=(server_id,))
        self.__manage_thread(t,server_id)
    
    def __manage_thread(self,t,server_id):
        "\""Function that starts the thread and updates the active thread count""\"
        #Updates Active thread count safely, and starts process
        with self.active_thread_count_lock[server_id]:
            self.active_thread_count[server_id]+=1  
        t.start()


    
    def clean(self,server_id):
        "\""Function to handle thread queing and thread ending logic.""\"

        with self.active_thread_count_lock[server_id]: #Reduces active thread count. Does this before restarting new thread to avoid double counting
            self.active_thread_count[server_id]-=1
        with self.__queue_lock[server_id]:

            for c in self.priority_levels:
                c= getattr(self,c)
                if len(c[server_id]) > 0:
                    task = c[server_id].pop(0)
                    self.create_thread(server_id,task)
                    return
        return
    
class AIGlobal(ProcessX):
    def __init__(self):
        super().__init__()

        methods = ['classify','converse','summarize','find_info']
        self.tasks = {method:getattr(self,method) for method in methods}

    def classify(self,input):
        return
 
    def converse(self,input):
        return
    
    def summarize(self,input):
        return
    
    def find_info(self,input):
        return

class DBGlobal(ProcessX):
    def __init__(self):
        super().__init__()
        self.db = Active()

"""




