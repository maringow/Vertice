import sqlite3
from sqlite3 import Error
import numpy as np


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


def add_column(conn, table_name, column_name, datatype):  # datatype options are text, integer, real
    try:
        cur = conn.cursor()
        cur.execute("ALTER TABLE {tn} ADD COLUMN {cn} {dt}".format(tn=table_name, cn=column_name, dt=datatype))
    except Error as e:
        print(e)

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


def select_max_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(scenario_id), MAX(run_id) FROM annual_forecast")
    row = cur.fetchall()

    return row

# sqlite3.register_adapter(np.int64, lambda val: int(val))  ## potential code for forcing int datatype

def insert_result(conn, results):
    print(results)
    sql = """INSERT INTO model_results(scenario_id, run_id, run_name, brand_name, molecule, dosage_form, 
    selected_NDCs, channel, indication, presentation, internal_external, brand_status, comments, vertice_filing_month, 
    vertice_filing_year, vertice_launch_month, vertice_launch_year, pos, exit_multiple, discount_rate,  
    tax_rate, base_year_volume, base_year_sales, volume_growth_rate, wac_price_growth_rate, api_cost_per_unit,  
    api_cost_unit, profit_margin_override, standard_cogs_entry, years_to_discount, cogs_increase, 
    gx_players_adj, npv, irr, payback)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, results)
    return cur.lastrowid


def insert_forecast(conn, annual_forecast):
    sql = """INSERT INTO annual_forecast(scenario_id, run_id, forecast_year, number_gx_competitors, profit_share,
            milestone_payments, research_development_cost, price_pct_of_mkt, net_sales, cogs, ebit, fcf, exit_value, moic)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, annual_forecast)
    return cur.lastrowid


model_results_ddl = """CREATE TABLE IF NOT EXISTS model_results (
                        id integer PRIMARY KEY,
                        scenario_id int NOT NULL,
                        run_id int NOT NULL,
                        timestamp text DEFAULT CURRENT_TIMESTAMP,
                        run_name text,
                        brand_name text,
                        molecule text NOT NULL,
                        dosage_form text,
                        selected_NDCs text,
                        channel text,
                        indication text,
                        presentation text,
                        internal_external text,
                        brand_status text,
                        comments text,
                        vertice_filing_month int,
                        vertice_filing_year int,
                        vertice_launch_month int,
                        vertice_launch_year int,
                        pos real,
                        exit_multiple real,
                        discount_rate real,
                        tax_rate real,
                        base_year_volume int,
                        base_year_sales real,
                        volume_growth_rate real,
                        wac_price_growth_rate real,
                        api_cost_per_unit real,
                        api_cost_unit real,
                        profit_margin_override real,
                        standard_cogs_entry real,
                        years_to_discount int,
                        cogs_increase real,
                        gx_players_adj int,
                        npv real,
                        irr real,
                        payback real
                        ); """


annual_forecast_ddl = """CREATE TABLE IF NOT EXISTS annual_forecast (
                            id integer PRIMARY KEY,
                            scenario_id int,
                            run_id int,
                            forecast_year int,
                            number_gx_competitors int,
                            profit_share real,
                            milestone_payments real,
                            research_development_cost real,
                            price_pct_of_mkt real,
                            net_sales real,
                            cogs real,
                            ebit real,
                            fcf real,
                            exit_value real,
                            moic real
                            ); """


