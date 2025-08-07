import sqlite3

conn = sqlite3.connect('sensai-ai/src/db/db.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall()]

print("Database tables:")
for table in tables:
    print(f"  - {table}")

required = ['users', 'organizations', 'user_organizations', 'cohorts', 'courses', 'tasks', 'questions']
missing = [t for t in required if t not in tables]

if missing:
    print(f"\n❌ Missing critical tables: {missing}")
else:
    print("\n✅ All critical authentication tables exist!")

conn.close()
