from time import sleep
def insert_new_time(conn, user_name: str, start_time: str, last_time: str, day_of_week):
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO time_table (user_name, start_time, last_time, day_of_week, current) VALUES (?, ?, ?, ?, ?)',
                   (user_name, start_time, last_time, day_of_week, True))
    conn.commit()
def select_times(conn, day_of_week, user_name=None, current=False):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """

    cursor = conn.cursor()
    if user_name is not None:
        if current:
            cursor.execute(f'SELECT * FROM time_table where user_name="{user_name}" and' +
                           f' day_of_week="{day_of_week}" and current=TRUE')
        else:
            cursor.execute(f'SELECT * FROM time_table where user_name="{user_name}" and day_of_week="{day_of_week}"')
    else:
        if current:
            cursor.execute(f'SELECT * FROM time_table where day_of_week="{day_of_week}" and current=TRUE')
        else:
            cursor.execute(f'SELECT * FROM time_table where day_of_week="{day_of_week}"')
    rows = cursor.fetchall()

    if len(rows)<=1:
        return rows

def select_user_time_table(conn, user_name, current=True):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """

    cursor = conn.cursor()
    if current:
        cursor.execute(f'SELECT * FROM time_table where user_name="{user_name}" and current=TRUE')
    else:
        cursor.execute(f'SELECT * FROM time_table where user_name="{user_name}"')
    rows = cursor.fetchall()

    return rows

def get_statistics(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """

    cursor = conn.cursor()
    cursor.execute('''SELECT day_of_week, SUM(current) 
                    FROM time_table where current=TRUE
                    GROUP BY day_of_week
                    ORDER BY 2 DESC;'''
                   )
    rows = cursor.fetchall()

    return rows

def make_non_current(conn, delay):
    while True:
        sql = f''' UPDATE time_table
                          SET current = FALSE'''
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        sleep(delay)
