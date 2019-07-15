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
    sql = """INSERT INTO model_results(brand_name, molecule, volume_growth_rate, npv)
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


model_results_ddl = """CREATE TABLE IF NOT EXISTS model_results (
                        id integer PRIMARY KEY,
                        run_id integer NOT NULL,
                        brand_name text,
                        molecule text NOT NULL,
                        channel text,
                        indication text,
                        presentation text,
                        comments text,
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
                        payback real
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
                            fcf real,
                            exit_value real,
                            moic real
                            ); """


conn = create_connection('C:\\sqlite\\db\\pythonsqlite.db')
select_all_results(conn)
conn.close()