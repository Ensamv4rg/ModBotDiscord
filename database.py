import psycopg2
from psycopg2 import extensions,pool
import os

from dotenv import load_dotenv
from threading import Lock
from datetime import datetime

delete_lock = Lock()
load_dotenv()

POSTGRES_URL = os.getenv('SERVER_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

class DatabaseInit:
    def __init__(self):
        self.connection = ''
        self.connect(server='main')
        self.setup()


    def connect(self,server='discord'):
        if server == 'main':
            connection=psycopg2.connect(POSTGRES_URL)
            connection.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = connection.cursor()
            try:
                cur.execute('CREATE DATABASE discord;')
                connection.commit()
            except psycopg2.errors.DuplicateDatabase:
                print("Database 'discord' already exists.")
            finally:
                cur.close()
                connection.close()

        else:
            self.connection=psycopg2.connect(DATABASE_URL)
        return self.connection

    def run_query(self, query,server = 'discord'):
        conn = self.connect(server)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query)
        except Exception as e:
            print(f"[ERROR] run_query failed for server={server!r}: {e}")
            raise
        finally:
            conn.close()


    def create_database(self):
        servers = """CREATE TABLE IF NOT EXISTS servers (
        server_id BIGINT PRIMARY KEY,
        user_who_invited_id BIGINT,
        mod_role BIGINT NULL);
        """
        topics = """CREATE TABLE IF NOT EXISTS topics (
        topic_id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE
        );
        """
        prohibited = """CREATE TABLE IF NOT EXISTS prohibited_server_topics (
        server_id  BIGINT REFERENCES servers(server_id),
        topic_id   INT REFERENCES topics(topic_id),
        PRIMARY KEY (server_id, topic_id)
        );
        """

        sessions = """CREATE TABLE IF NOT EXISTS sessions(
        server_id BIGINT,
        date_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        deactivated_at TIMESTAMP NULL,
        is_active BOOL DEFAULT True
        );"""
        queries = [servers,topics,prohibited,sessions]

        for query in queries:
            stop = query.find('(')
            content = query[:stop]

            try:
                self.run_query(query)
                print(f'Query {content} completed')
            except Exception as e:
                print(f"Couldn't complete query {content} due to error: {e}")
                continue
        return True
        
    def setup(self):
        if not (self.create_database()):
            print("Error Creating Database")
        else:
            print("Database created succesfully!")

def create_db():
    DatabaseInit()

class Active():

    """This Class represents an active database session for a server."""

    def __init__(self,server_id,minconn=1, maxconn=11):
        self.discord_pool = pool.SimpleConnectionPool(minconn, maxconn, dsn=DATABASE_URL) #Creates a connection pool rather than opening a new connection whenever a new transaction is initiated
        self.server_id = server_id
        self.add_session()

    def _get_pool(self):
        return self.discord_pool

    def run_query(self,query,values=None,verbose=False):
        try:
            conn_pool = self._get_pool()
            conn = conn_pool.getconn()

            cur = conn.cursor()

            if values is not None:
                cur.execute(query,values)
            else:
                cur.execute(query)
            
            if verbose:
                print(f"Query: {query} completed succesfully")
            conn.commit()
            if cur.description:
                out= cur.fetchall() #Returns for queries that require fetching of data
                return out
        except Exception as e:
            print(f"Query {query} uncompleted with error: {e}")
            raise

        finally:
            conn_pool.putconn(conn) #Returns the connection to the pool of connections



#INSERT Queries
    #ADD SERVER
    def add_server(self,inviter_id):
        query = "INSERT INTO servers (server_id, user_who_invited_id) VALUES (%s, %s) ON CONFLICT (server_id) DO NOTHING;"
        values = (self.server_id,inviter_id)
        self.run_query(query,values)

    def add_server_role_id(self,role_id):
        query = "UPDATE servers SET mod_role = %s WHERE server_id = %s;"
        values = (role_id, self.server_id)
        self.run_query(query, values)


    #ADD TOPIC
    def add_topic(self, name, id=None):
        if id is not None:
            query = "INSERT INTO topics (topic_id, name) VALUES (%s, %s);"
            values = (id, name)
        else:
            query = "INSERT INTO topics (name) VALUES (%s);"
            values = (name,)

        self.run_query(query, values)

        query2 = """
            SELECT setval(
                pg_get_serial_sequence('topics','topic_id'),
                GREATEST((SELECT MAX(topic_id) FROM topics), 1),
                true
            );
        """
        self.run_query(query2)



    #ADD TOPIC FOR SERVER
    def add_topic_for_server(self,topic_id):
        query = "INSERT INTO prohibited_server_topics (server_id, topic_id) VALUES (%s, %s);"
        values = (self.server_id,topic_id)
        self.run_query(query,values)
    


#DELETE QUERIES
    #REMOVE SERVER
    def remove_server(self):
        with delete_lock:
            query = "DELETE FROM prohibited_server_topics WHERE server_id=%s;"
            self.run_query(query,(self.server_id,))
            query ="DELETE FROM servers WHERE server_id = %s"
            self.run_query(query,(self.server_id,))
        self.deactivate_session(datetime.now())
    #REMOVE TOPIC
    def remove_topic(self,topic_id):
        with delete_lock:
            query = "DELETE FROM prohibited_server_topics WHERE topic_id = %s;"
            self.run_query(query,(topic_id,))
            query = "DELETE FROM topics WHERE topic_id = %s;"
            self.run_query(query,(topic_id,))


    #REMOVE TOPIC FOR SERVER
    def remove_topic_for_server(self,topic_id):
        with delete_lock:
            query= "DELETE FROM prohibited_server_topics WHERE server_id= %s AND topic_id = %s"
            values = (self.server_id,topic_id)
            self.run_query(query,values)


#FETCH QUERIES
    #Return all Server's Topics as list
    def return_topics_for_server(self):
        query = "SELECT topic_id FROM prohibited_server_topics WHERE server_id = %s"
        values = (self.server_id,)
        return [value[0] for value in self.run_query(query,values)]
    
    def get_topic_name(self,topic_id):
        query = "SELECT name FROM topics WHERE topic_id = %s"
        values = (topic_id,)
        return self.run_query(query,values)[0][0] 
    

#SESSION QUERIES
    #ADD Session info to database
    def add_session(self):
        query = "INSERT INTO sessions (server_id) VALUES (%s)"
        values = (self.server_id,)
        self.run_query(query,values)


    #Deactivate session
    def deactivate_session(self,timestamp):
        query = "UPDATE sessions SET deactivated_at=%s WHERE server_id=%s"
        self.run_query(query,(timestamp,self.server_id))
        query = "UPDATE sessions SET is_active=FALSE WHERE server_id=%s"
        self.run_query(query,(self.server_id,))

    def delete_session(self):
        query = "DELETE FROM sessions WHERE server_id=%s"
        self.run_query(query,(self.server_id,))

    #Get session info
    def get_details(self):
        query = "SELECT * FROM sessions WHERE server_id=%s;"
        sessionz = self.run_query(query,(self.server_id,))
        output = [session for session in sessionz][0]
        return output

    
   

#Close Connecion
    def close_pool(self):
        self.discord_pool.closeall()

def restart_session(oldsession):
    server_id = oldsession.server_id 
    oldsession.close_pool()
    new_session= Active(server_id)
    return new_session



def create_session(server_id=None):
    if server_id is None:
        session = Active()
    else:
        session = Active(server_id)
    return session

create_db() 