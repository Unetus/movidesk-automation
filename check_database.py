"""Quick script to verify database content."""
import sqlite3

conn = sqlite3.connect('data/automation.db')
cursor = conn.cursor()

print("="*60)
print("REPORTS TABLE")
print("="*60)
rows = cursor.execute('''
    SELECT id, generated_at, total_new, total_overdue, 
           total_expiring, total_summarized, email_sent
    FROM reports
    ORDER BY generated_at DESC
    LIMIT 5
''').fetchall()
for row in rows:
    print(f"ID: {row[0]} | Date: {row[1]}")
    print(f"  New: {row[2]}, Overdue: {row[3]}, Expiring: {row[4]}, Summarized: {row[5]}")
    print(f"  Email sent: {row[6]}")
    print()

print("="*60)
print("AI_SUMMARIES TABLE")
print("="*60)
rows = cursor.execute('''
    SELECT ticket_id, ticket_number, use_count, 
           LENGTH(summary) as summary_len, model_used
    FROM ai_summaries
    ORDER BY generated_at DESC
''').fetchall()
for row in rows:
    print(f"Ticket #{row[1]} (ID: {row[0]})")
    print(f"  Use count: {row[2]} | Summary length: {row[3]} chars | Model: {row[4]}")
    print()

print("="*60)
print("REPORT_TICKETS TABLE")
print("="*60)
total = cursor.execute('SELECT COUNT(*) FROM report_tickets').fetchone()[0]
print(f"Total tickets saved: {total}")
print()

# Get sections breakdown
sections = cursor.execute('''
    SELECT section, COUNT(*) as count
    FROM report_tickets
    GROUP BY section
''').fetchall()
print("Breakdown by section:")
for section, count in sections:
    print(f"  {section}: {count}")

conn.close()
