import sqlite3

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)  #Make it multi thread accessible

# obj = conn.execute('''
# select *, current_timestamp from thread_names
# ''')

# for row in obj:
#     print(row)

# conn.execute('''
# drop table thread_names
# ''')

# conn.commit()

# conn.execute('''
# delete from thread_names
# ''')

conn.execute('''
delete from checkpoints
''')

conn.commit()