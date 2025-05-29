from database import Active

class Session_Manager():
    def __init__(self):
        self.sessions = {}
   
    def add_session(self,server_id):
        self.sessions[server_id] = Active(server_id)
    
    def remove_session(self,server_id):
        self.sessions[server_id].close_pool()
        del self.sessions[server_id]

    def restart_session(self,server_id):
        self.sessions[server_id] = self.sessions[server_id].restart_session()
    
    def __str__(self,verbose=False):
        n_of_sess = len(self.sessions)
        if not verbose:
            return f"""{n_of_sess} sessions opens"""
        else:
            details = "\n".join( [f"Server ID: {key}" for key in self.sessions.keys])
            return f"""{n_of_sess} sessions opened! Details below
                       {details} """