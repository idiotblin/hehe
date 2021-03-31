import psycopg2, os, datetime, time

conn = psycopg2.connect(
    f'dbname={os.environ["Dbname"]} user={os.environ["User"]} password={os.environ["Password"]} host={os.environ["Host"]} port={os.environ["Port"]}')
cur = conn.cursor()


def prime(n):
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


while True:
    cur.execute(f"select * from work where status='Queued';")
    task = cur.fetchall()
    if len(task) > 0:
        task = task[0]
        id = task[0]
        date = task[1]
        n = task[2]
        email = task[7]
        cur.execute(f"delete from work where id={id};")
        conn.commit()
        cur.execute(f"insert into work(time, N, status, email) values ('{date}', {n}, 'Processing', '{email}');")
        conn.commit()
        begin = datetime.datetime.now().second
        for p in range(2, int(n ** 0.5) + 1):
            q = n // p
            if q * p == n and prime(p) and prime(q):
                end = datetime.datetime.now().second
                cur.execute(f"delete from work where n={n} and status='Processing';")
                conn.commit()
                cur.execute(f"insert into work(time, N, p, q, status, elapsed, email) values ('{date}', {n}, {p}, {q}, 'Done', '{end - begin}', '{email}');")
                conn.commit()
                i = n
    time.sleep(5)
