import database
from database import Active

from database import Session_Manager
import random
from random import choice
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(threadName)s: %(message)s')

def test_database():
    """This function is used to handle tests involving all database operations save operations for session management"""
    # Create Database Properly
    database.create_db()

    all_topics = [f"Topic_{pos}" for pos in range(1, 23)]
    print(all_topics)
    global length
    length = len(all_topics)
    ids = [num for num in range(1, 12)]

    NUM_THREADS = 11
    add_barrier = threading.Barrier(NUM_THREADS)

    def test(thread_number, refresh=False, length=23):
        if refresh:
            thread_number = thread_number + 11  # Avoid duplication errors.
        else:
            length = length // 2

        server_id = thread_number + 1  # Now passed to Active class
        session = database.create_session(server_id)  # Updated: session is created per thread with server_id

        try:
            chosen_role_id = choice(ids)
            chosen_inviter_id = choice(ids)
            chosen_number_of_topics = choice(ids)

            session.add_topic(id=thread_number + 1, name=all_topics[thread_number])
            try:
                add_barrier.wait(timeout=10)
            except threading.BrokenBarrierError:
                logging.error(f"Thread {thread_number}: Timed out waiting at the barrier.")
                return

            session.remove_topic(thread_number + 1)
            session.add_topic(id=thread_number + 1, name=all_topics[thread_number])
            logging.info(f"Thread:{thread_number} Topic Handling Passed!")

            session.add_server(chosen_inviter_id)
            session.add_server_role_id(chosen_role_id)
            logging.info(f"Thread:{thread_number} Adding Servers Passed!")

            topic_ids = random.sample(range(1, length), min(chosen_number_of_topics, length))
            for val in topic_ids:
                session.add_topic_for_server(val)
            logging.info(f"Thread:{thread_number} Adding topics for servers passed!")

            topics = session.return_topics_for_server()
            logging.info(f"Thread:{thread_number} Returning topics successful!")

            names = [session.get_topic_name(topic) for topic in topics]
            logging.info(f'Thread:{thread_number} Topics for server {server_id}: {names}')

            session.remove_topic_for_server(choice(topics))
            remaining = [session.get_topic_name(topic) for topic in session.return_topics_for_server()]
            logging.info(f"After cleanup, topics table has entries for server {server_id}: {remaining}")
            if len(remaining) == len(topics) - 1:
                logging.info(f'Thread:{thread_number} Topic deletion for server is successful')
            else:
                raise Exception("Couldn't delete topics")

            session.remove_server()
            logging.info(f'Removing Server Passed!')
            logging.info('All tests passed\n')

        except Exception as e:
            logging.error(f"Thread {thread_number} unsuccessful with Error {e}")
        finally:
            session.close_pool()  # Clean up each thread's connection pool

    def exec_tests(refresh=False):
        threads = [threading.Thread(target=test, args=(i, refresh)) for i in range(NUM_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    exec_tests()

    try:
        # Session restart is now per server_id
        for i in range(NUM_THREADS):
            server_id = i + 12  # Because we offset by 11 in the second round
            old_session = database.create_session(server_id)
            session = database.restart_session(old_session)
            session.close_pool()
        exec_tests(refresh=True)
    except Exception as e:
        print('Session Restart failed:', e)

def test_session_manager():
    def run_operations_for_session(session, session_id, thread_index, has_server=True):
        """This function runs operations on a given session instance. Can run in threads."""
        all_topics = [f"Topic_{pos}" for pos in range(1, 23)]
        ids = [num for num in range(1, 12)]
        try:
            # Calculate a unique topic ID per thread within the session
            topic_id = session_id * 10 + thread_index + 1
            topic_name = f"Topic_{topic_id}"
            chosen_role_id = choice(ids)
            chosen_inviter_id = choice(ids)
            chosen_number_of_topics = choice(ids)
            length = len(all_topics)

            session.add_topic(id=topic_id, name=topic_name)
            session.remove_topic(topic_id)
            session.add_topic(id=topic_id, name=topic_name)
            logging.info(f"Session:{session_id} Thread:{thread_index} Topic Handling Passed!")

            session.add_server(chosen_inviter_id) if has_server else None
            session.add_server_role_id(chosen_role_id)
            logging.info(f"Session:{session_id} Thread:{thread_index} Adding Roles Passed!")

            if has_server:
                topic_ids = random.sample(range(1, length), min(chosen_number_of_topics, length))
                for val in topic_ids:
                    session.add_topic_for_server(val)

                topics = session.return_topics_for_server()
                logging.info(f"Session:{session_id} Thread:{thread_index} Topics for server: {topics}")

                session.remove_topic_for_server(choice(topics))
                remaining = session.return_topics_for_server()
                if len(remaining) == len(topics) - 1:
                    logging.info(f'Session:{session_id} Thread:{thread_index} Topic deletion success')
                else:
                    raise Exception("Couldn't delete topics")

                session.remove_server()
                logging.info(f'Session:{session_id} Thread:{thread_index} Server removal Passed!')

        except Exception as e:
            logging.error(f"Session:{session_id} Thread:{thread_index} operation error: {e}")
        finally:
            session.close_pool()

    def test_session_managing():
        """Test true multi-session, multi-threaded environment"""
        NUM_SESSIONS = 5
        THREADS_PER_SESSION = 3

        def session_worker(session_id):
            session = database.create_session(session_id)
            threads = [
                threading.Thread(
                    target=run_operations_for_session,
                    args=(session, session_id, i),
                    kwargs={'has_server': True if i % 2 == 0 else False}
                )
                for i in range(THREADS_PER_SESSION)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        outer_threads = [
            threading.Thread(target=session_worker, args=(sid,))
            for sid in range(1, NUM_SESSIONS + 1)
        ]
        for t in outer_threads:
            t.start()
        for t in outer_threads:
            t.join()

        logging.info("All multi-session operations completed.")

    test_session_managing()

def run_all_tests():
    """Run both test_database and test_session_manager sequentially."""
    logging.info("Starting database tests...")
    test_database()
    logging.info("Database tests completed. Starting session manager tests...")
    test_session_manager()
    logging.info("All tests completed.")

# Uncomment the line below to run the tests when the script is executed
run_all_tests()