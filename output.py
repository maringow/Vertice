import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    # create a database connection to a SQLite database
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def insert_result(conn, results):
    sql = """INSERT INTO model_results(run_id, brand_name, molecule, NPV)
            VALUES(?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, results)
    conn.commit()
    return cur.lastrowid


def insert_forecast(conn, annual_forecast):
    sql = """INSERT INTO annual_forecast(result_id, run_id, forecast_year, number_gx_competitors, profit_share,
            net_sales, cogs)
            VALUES(?,?,?,?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, annual_forecast)
    conn.commit()
    return cur.lastrowid

def select_all_results(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM model_results")
    rows = cur.fetchall()

    for row in rows:
        print(row)

def select_all_forecasts(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM annual_forecast")
    rows = cur.fetchall()

    for row in rows:
        print(row)


conn = create_connection('C:\\sqlite\\db\\pythonsqlite.db')

model_results_ddl = """CREATE TABLE IF NOT EXISTS model_results (
                        id integer PRIMARY KEY,
                        run_id integer NOT NULL,
                        brand_name text,
                        molecule text NOT NULL,
                        channel text,
                        indication text,
                        presentation text,
                        comments text,
                        gx_competitors integer,
                        vertice_filing_month integer,
                        vertice_filing_year integer,
                        vertice_launch_year integer,
                        vertice_launch_month integer,
                        pos real,
                        base_year_volume,
                        base_year_sales,
                        volume_growth_rate real,
                        wac_price_growth_rate real,
                        per_unit_cogs real,
                        npv real,
                        irr real,
                        payback real,
                        exit_value real,
                        moic real
                        ); """


annual_forecast_ddl = """CREATE TABLE IF NOT EXISTS annual_forecast (
                            id integer PRIMARY KEY,
                            result_id integer,
                            run_id integer,
                            forecast_year integer,
                            number_gx_competitors integer,
                            profit_share real,
                            milestone_payments real,
                            research_development_cost real,
                            net_sales real,
                            cogs real,
                            ebit real,
                            fcf real
                            ); """


create_table(conn, model_results_ddl)
create_table(conn, annual_forecast_ddl)

result1 = (101, 'WATER', 'H20', 45.6)
result2 = (102, 'GLEEVEC', 'IMATINIB', 127.3)
insert_result(conn, result1)
insert_result(conn, result2)

annual1 = (101, 1000, 2019, 2, .25, 190000, 45000)
annual2 = (101, 1000, 2020, 3, .25, 250000, 65000)
insert_forecast(conn, annual1)
insert_forecast(conn, annual2)

select_all_results(conn)
select_all_forecasts(conn)

# result3 = (103, 'WATER', 'H20', 45.6)
# result4 = (104, 'GLEEVEC', 'IMATINIB', 127.3)
# insert_result(conn, result3)
# insert_result(conn, result4)
# select_all_results(conn)

conn.close()
