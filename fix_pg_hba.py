import subprocess

hba_content = "local   all             all                                     trust\nhost    all             all             127.0.0.1/32            trust\nhost    all             all             ::1/128                 trust\nhost    all             all             0.0.0.0/0               trust\nlocal   replication     all                                     trust\nhost    replication     all             127.0.0.1/32            trust\nhost    replication     all             ::1/128                 trust\n"

with open("pg_hba_new.conf", "w") as f:
    f.write(hba_content)

subprocess.run(["docker", "cp", "pg_hba_new.conf", "medical_postgres:/var/lib/postgresql/data/pg_hba.conf"])
subprocess.run(["docker", "exec", "medical_postgres", "psql", "-U", "postgres", "-c", "SELECT pg_reload_conf();"])
print("Done!")