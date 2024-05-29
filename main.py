import time
import psycopg2
from faker import Faker
from decouple import config
import matplotlib.pyplot as plt


DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_HOST = config('DB_HOST')
DB_PORT = config('DB_PORT', default='5432')
DB_SCHEMA = config('DB_SCHEMA', default='public')


conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    options=f"-c search_path={DB_NAME},{DB_SCHEMA}"
)


cur = conn.cursor()

# Generar datos aleatorios
fake = Faker('es_MX')


def create_table():
    cur.execute("""
    DROP TABLE IF EXISTS sentences;
    CREATE TABLE sentences (
        id serial PRIMARY KEY,
        sentence text,
        sentence_indexed text
    )
    """)
    cur.execute("""
    CREATE INDEX gin_sentence_idx ON sentences USING GIN (sentence_indexed gin_trgm_ops);
    """)
    conn.commit()


def insert_data(num_records):
    for _ in range(num_records):
        text = fake.sentence(nb_words=10)
        cur.execute("INSERT INTO sentences (sentence, sentence_indexed) VALUES (%s, %s)", (text, text))
    conn.commit()

# Medir tiempos de ejecución
def measure_time(query):
    start_time = time.time()
    cur.execute(query)
    conn.commit()
    end_time = time.time()
    return end_time - start_time

# Tiempos de ejecución para diferentes tamaños de datos
n_record = [10, 100, 1000, 10000, 100000]
times_without_index = []
times_with_index = []

random_word = fake.word()
print(f"Palabra aleatoria: {random_word}")

for n in n_record:
    print(f"Generando {n} registros...")
    create_table()
    insert_data(n)

    time_without_index = measure_time(f"SELECT * FROM sentences WHERE sentence LIKE '%{random_word}%'")
    times_without_index.append(time_without_index)
    
    time_with_index = measure_time(f"SELECT * FROM sentences WHERE sentence_indexed LIKE '%{random_word}%'")
    times_with_index.append(time_with_index)

cur.close()
conn.close()

plt.plot(n_record, times_without_index, label='Sin Índice')
plt.plot(n_record, times_with_index, label='Con Índice GIN')
plt.xlabel('Número de Registros')
plt.ylabel('Tiempo de Ejecución (s)')
plt.title('Comparación de Tiempos de Ejecución')
plt.legend()
plt.show()