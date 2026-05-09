#!/usr/bin/env python3
"""
Read Complete Database Schema from MySQL
This script connects to the MySQL database and extracts:
- All tables
- All columns with types
- All indexes
- All foreign keys
- Table relationships
"""
import os
import sys
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

def read_complete_schema():
    """Read complete database schema"""
    
    # Get database configuration from environment
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'client_0000000002')
    
    print(f"\n🔍 Connecting to database...")
    print(f"   Host: {db_host}:{db_port}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    
    # Build connection string
    connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    
    try:
        # Create engine
        engine = create_engine(connection_string, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Connected successfully!\n")
        
        # Get inspector
        inspector = inspect(engine)
        
        # Get all table names
        tables = inspector.get_table_names()
        
        if not tables:
            print(f"⚠️  No tables found in database '{db_name}'")
            print("\nMake sure you're connected to the correct database.")
            return None
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        print("\n" + "="*80)
        print("COMPLETE DATABASE SCHEMA")
        print("="*80 + "\n")
        
        schema_doc = {
            'database': db_name,
            'tables': {},
            'relationships': []
        }
        
        # Process each table
        for table_name in sorted(tables):
            print(f"\n📋 Table: {table_name}")
            print("-" * 80)
            
            table_info = {
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': []
            }
            
            # Get columns
            columns = inspector.get_columns(table_name)
            print(f"\nColumns ({len(columns)}):")
            for col in columns:
                col_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col['default']) if col.get('default') else None,
                    'autoincrement': col.get('autoincrement', False)
                }
                table_info['columns'].append(col_info)
                
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                default_str = f"DEFAULT {col['default']}" if col.get('default') else ""
                auto_str = "AUTO_INCREMENT" if col.get('autoincrement') else ""
                
                print(f"  • {col['name']:30} {str(col['type']):20} {nullable_str:10} {default_str} {auto_str}")
            
            # Get primary keys
            pk = inspector.get_pk_constraint(table_name)
            if pk and pk.get('constrained_columns'):
                table_info['primary_keys'] = pk['constrained_columns']
                print(f"\nPrimary Key: {', '.join(pk['constrained_columns'])}")
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"\nForeign Keys ({len(fks)}):")
                for fk in fks:
                    fk_info = {
                        'name': fk.get('name'),
                        'columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    table_info['foreign_keys'].append(fk_info)
                    
                    print(f"  • {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
                    
                    schema_doc['relationships'].append({
                        'from_table': table_name,
                        'from_columns': fk['constrained_columns'],
                        'to_table': fk['referred_table'],
                        'to_columns': fk['referred_columns']
                    })
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print(f"\nIndexes ({len(indexes)}):")
                for idx in indexes:
                    idx_info = {
                        'name': idx['name'],
                        'columns': idx['column_names'],
                        'unique': idx.get('unique', False)
                    }
                    table_info['indexes'].append(idx_info)
                    
                    unique_str = "UNIQUE" if idx.get('unique') else ""
                    print(f"  • {idx['name']:40} on ({', '.join(idx['column_names'])}) {unique_str}")
            
            schema_doc['tables'][table_name] = table_info
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Tables: {len(tables)}")
        print(f"Total Relationships: {len(schema_doc['relationships'])}")
        
        # Save to JSON file
        json_file = 'database_schema_complete.json'
        with open(json_file, 'w') as f:
            json.dump(schema_doc, f, indent=2, default=str)
        print(f"\n✅ Complete schema saved to: {json_file}")
        
        # Generate markdown documentation
        md_file = 'DATABASE_SCHEMA_COMPLETE.md'
        with open(md_file, 'w') as f:
            f.write(f"# Complete Database Schema: {db_name}\n\n")
            f.write(f"**Total Tables**: {len(tables)}\n\n")
            f.write("---\n\n")
            
            for table_name in sorted(tables):
                table = schema_doc['tables'][table_name]
                f.write(f"## Table: `{table_name}`\n\n")
                
                # Columns
                f.write("### Columns\n\n")
                f.write("| Column | Type | Nullable | Default | Notes |\n")
                f.write("|--------|------|----------|---------|-------|\n")
                for col in table['columns']:
                    notes = []
                    if col['name'] in table['primary_keys']:
                        notes.append('**PRIMARY KEY**')
                    if col['autoincrement']:
                        notes.append('AUTO_INCREMENT')
                    
                    nullable = "✅ Yes" if col['nullable'] else "❌ No"
                    default = col['default'] if col['default'] else "-"
                    notes_str = ", ".join(notes) if notes else "-"
                    
                    f.write(f"| `{col['name']}` | {col['type']} | {nullable} | {default} | {notes_str} |\n")
                
                # Foreign Keys
                if table['foreign_keys']:
                    f.write("\n### Foreign Keys\n\n")
                    for fk in table['foreign_keys']:
                        f.write(f"- `{', '.join(fk['columns'])}` → `{fk['referred_table']}.{', '.join(fk['referred_columns'])}`\n")
                
                # Indexes
                if table['indexes']:
                    f.write("\n### Indexes\n\n")
                    for idx in table['indexes']:
                        unique = "UNIQUE " if idx['unique'] else ""
                        f.write(f"- {unique}`{idx['name']}` on ({', '.join(idx['columns'])})\n")
                
                f.write("\n---\n\n")
            
            # Relationships diagram
            if schema_doc['relationships']:
                f.write("## Database Relationships\n\n")
                f.write("```\n")
                for rel in schema_doc['relationships']:
                    f.write(f"{rel['from_table']}.{', '.join(rel['from_columns'])} -> {rel['to_table']}.{', '.join(rel['to_columns'])}\n")
                f.write("```\n\n")
        
        print(f"✅ Markdown documentation saved to: {md_file}")
        
        return schema_doc
        
    except SQLAlchemyError as e:
        print(f"\n❌ Database Error: {e}")
        print("\nPossible issues:")
        print("1. MySQL not installed or not running")
        print("2. Database credentials incorrect in .env file")
        print("3. Database doesn't exist")
        print(f"4. User '{db_user}' doesn't have access to database '{db_name}'")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == '__main__':
    print("\n" + "="*80)
    print("DATABASE SCHEMA READER")
    print("="*80)
    
    schema = read_complete_schema()
    
    if schema:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print("\nFiles generated:")
        print("  1. database_schema_complete.json - Machine-readable schema")
        print("  2. DATABASE_SCHEMA_COMPLETE.md - Human-readable documentation")
        print("\nNext step: Load this schema into the AI knowledge base")
    else:
        print("\n❌ Failed to read database schema")
        sys.exit(1)

