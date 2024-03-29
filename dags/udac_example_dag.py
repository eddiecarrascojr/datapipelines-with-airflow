from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import (StageToRedshiftOperator, LoadFactOperator, LoadDimensionOperator, DataQualityOperator)
from helpers import SqlQueries

# AWS_KEY = os.environ.get('AWS_KEY')
# AWS_SECRET = os.environ.get('AWS_SECRET')
start_date = datetime.utcnow()

default_args = {
    'owner': 'udacity',
    'depends_on_past' : False,
    'retries' : 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2019, 1, 12),
    'email_on_retry' : False
}

dag = DAG('udac_example_dag',
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
          schedule_interval='0 * * * *',
          catchup=False
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

stage_events_to_redshift = StageToRedshiftOperator(
    task_id='Stage_events',
    dag=dag,
    redshift_conn_id = "redshift",
    table="events",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="log_data",
    region="us-west-2",
    file_format="JSON",
    execution_date=start_date)

stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='Stage_songs',
    dag=dag,
    table="songs",
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="song_data",
    region="us-west-2",
    data_format="JSON",
    execution_date=start_date)

load_songplays_table = LoadFactOperator(
    task_id='Load_songplays_fact_table',
    dag=dag,aws_credentials_id="aws_credentials",
    redshift_conn_id='redshift',
    sql_query=SqlQueries.songplay_table_insert)

load_user_dimension_table = LoadDimensionOperator(
    task_id='Load_user_dim_table',
    dag=dag,
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    start_date= datetime(2018, 5, 1),
    table="users",
    sql_query=SqlQueries.user_table_insert)

load_song_dimension_table = LoadDimensionOperator(
    task_id='Load_song_dim_table',
    dag=dag,
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    table="songs",
    start_date= datetime(2018, 5, 1),
    sql_query=SqlQueries.song_table_insert)

load_artist_dimension_table = LoadDimensionOperator(
    task_id='Load_artist_dim_table',
    dag=dag,
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    table="artist",
    start_date= datetime(2018, 5, 1),
    sql_query=SqlQueries.artist_table_insert)

load_time_dimension_table = LoadDimensionOperator(
    task_id='Load_time_dim_table',
    dag=dag,
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    table="time",
    start_date= datetime(2018, 5, 1),
    sql_query=SqlQueries.artist_table_insert)

run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    dag=dag,
    aws_credentials_id="aws_credentials",
    redshift_conn_id='redshift',
    tables=["songplay", "users", "song", "artist", "time"])

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

# Start dependecies
start_operator >> [stage_songs_to_redshift, stage_events_to_redshift]

[stage_events_to_redshift, stage_songs_to_redshift] >> load_songplays_table

load_songplays_table >> [load_user_dimension_table, load_song_dimension_table, load_artist_dimension_table,
                           load_time_dimension_table] >> run_quality_checks

run_quality_checks >> end_operator