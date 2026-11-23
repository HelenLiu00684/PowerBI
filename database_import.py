import os
from getpass import getpass

from sqlalchemy import URL, create_engine, text
from sqlalchemy import Column, Date, String, inspect
from sqlalchemy.orm import DeclarativeBase

from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Read the password from the environment.
# If it is unavailable, ask for hidden keyboard input.
password = os.environ.get("MSSQL_SA_PASSWORD")
if not password:
    password = getpass("SQL Server administrator password: ")

# Build the connection configuration.
# Port 14333 is the published Docker port.
# Connect to the existing master database for this initial test.
connection_url = URL.create(
    drivername="mssql+pyodbc",
    username="sa",
    password=password,
    host="localhost",
    port=14333,
    database="master",
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "Encrypt": "yes",
        # Trust the server certificate for this local development setup.
        "TrustServerCertificate": "yes",
    },
)

# Create the engine. The actual connection opens below.
engine = create_engine(connection_url)

# Open a connection and ask SQL Server for the current database name.
# The with block returns the connection to the pool when it finishes.
with engine.connect() as connection:
    database_name = connection.execute(
        text("SELECT DB_NAME()")
    ).scalar_one()

    print("Connection successful.")
    print("Current database:", database_name)

# CREATE DATABASE must run outside a transaction.
# AUTOCOMMIT allows SQL Server to execute this statement directly.
with engine.connect().execution_options(
    isolation_level="AUTOCOMMIT"
) as connection:

    # Create the project database only if it does not already exist.
    # Running this script again will preserve the existing database.
    connection.execute(
        text("""
            IF DB_ID(N'CourseAnalytics') IS NULL
            BEGIN
                CREATE DATABASE [CourseAnalytics];
            END
        """)
    )

    # Confirm that the database exists.
    database_name = connection.execute(
        text("SELECT name FROM sys.databases WHERE name = N'CourseAnalytics'")
    ).scalar_one()

    print("Project database is ready:", database_name)

# Release the connection pool.
engine.dispose()

# Define the base class shared by ORM models.
# Base.metadata stores the table definitions.
class Base(DeclarativeBase):
    pass


# Each Registration object represents one course registration.
class Registration(Base):

    # Set the SQL Server table name.
    __tablename__ = "Registrations"

    # RegistrationID uniquely identifies each registration.
    # A primary key cannot be missing or duplicated.
    RegistrationID = Column(String(20), primary_key=True)

    # Allow unresolved missing values to remain SQL NULL.
    # Example: a missing StudentID stays NULL rather than being invented.
    StudentID = Column(String(20), nullable=True)
    Program = Column(String(100), nullable=True)

    # CourseID is required in the current dataset.
    CourseID = Column(String(20), nullable=False)
    CourseName = Column(String(200), nullable=True)

    # Store the term label as text, such as "2025-Winter".
    Term = Column(String(20), nullable=False)

    # Use SQL DATE columns for dates, rather than storing them as text.
    RegistrationDate = Column(Date, nullable=True)
    CourseStartDate = Column(Date, nullable=False)
    CourseEndDate = Column(Date, nullable=False)

    Status = Column(String(30), nullable=True)

    # The text "None" means no prerequisite is required.
    # SQL NULL means the prerequisite information is missing.
    PrerequisiteCourses = Column(String(500), nullable=True)


# Reuse the connection settings, but select the project database.
project_url = connection_url.set(database="CourseAnalytics")
project_engine = create_engine(project_url)

# Create the tables defined in Base.metadata if they do not exist.
# This does not insert registration records.
Base.metadata.create_all(project_engine)

# Read the actual table structure from SQL Server.
inspector = inspect(project_engine)
columns = inspector.get_columns("Registrations", schema="dbo")

print("\nRegistrations table is ready.")
print("Number of columns:", len(columns))

# Display each column's name, SQL type, and missing-value allowance.
for column in columns:
    print(
        f"{column['name']}: "
        f"type={column['type']}, "
        f"nullable={column['nullable']}"
    )

# Locate the cleaned CSV relative to this script.
csv_path = (
    Path(__file__).resolve().parent
    / "output"
    / "registrations_prepared.csv"
)

# Preserve literal text such as "None".
# Only empty CSV fields are treated as missing values.
df = pd.read_csv(
    csv_path,
    encoding="utf-8-sig",
    dtype="string",
    keep_default_na=False,
    na_values=[""],
)

# Select the columns defined in the ORM model.
# Additional review columns, if present, are not imported.
table_columns = [
    column.name for column in Registration.__table__.columns
]
df = df[table_columns].copy()

# Convert the cleaned date text into Python date objects.
# An invalid non-empty date stops the import for investigation.
date_columns = [
    "RegistrationDate",
    "CourseStartDate",
    "CourseEndDate",
]

for column in date_columns:
    df[column] = pd.to_datetime(
        df[column],
        format="%Y-%m-%d",
        errors="raise",
    ).dt.date

# Convert pandas missing values into Python None.
# The database driver stores Python None as SQL NULL.
# The literal string "None" remains text.
df = df.astype(object).where(df.notna(), None)

# Convert each row into a dictionary.
# Example:
# {"RegistrationID": "R000001", "StudentID": "S0001", ...}
records = df.to_dict(orient="records")

# Open a session and begin a transaction.
# Validate registration IDs before writing to the database.
# Every CSV row must have one non-empty, unique registration ID.
registration_ids = df["RegistrationID"]

invalid_id_mask = (
    registration_ids.isna()
    | registration_ids.str.strip().eq("").fillna(False)
)

if invalid_id_mask.any():
    raise ValueError(
        "Import stopped: the CSV contains missing or empty registration IDs."
    )

if registration_ids.duplicated().any():
    raise ValueError(
        "Import stopped: the CSV contains duplicate registration IDs."
    )

# Track how many records are inserted, updated, or unchanged.
inserted_count = 0
updated_count = 0
unchanged_count = 0

# Update attributes only; RegistrationID remains the lookup key.
update_columns = [
    column for column in table_columns
    if column != "RegistrationID"
]

try:
    # Commit all changes on success.
    # Roll back all changes if an exception occurs.
    with Session(project_engine) as session:
        with session.begin():

            # Load existing ORM objects once.
            # This is practical for our small demonstration dataset.
            existing_registrations = session.scalars(
                select(Registration)
            ).all()

            # Build a lookup dictionary using RegistrationID as the key.
            # Example:
            # "R000001" -> the existing Registration object
            existing_by_id = {
                registration.RegistrationID: registration
                for registration in existing_registrations
            }

            database_count_before = len(existing_by_id)

            # Process one CSV record at a time.
            for record in records:
                registration_id = record["RegistrationID"]
                registration = existing_by_id.get(registration_id)

                # A new registration ID requires an INSERT.
                if registration is None:
                    session.add(Registration(**record))
                    inserted_count += 1
                    continue

                # An existing registration may require an UPDATE.
                record_changed = False

                for column in update_columns:
                    # Read the current ORM attribute and incoming CSV value.
                    # Example: column is "Program".
                    old_value = getattr(registration, column)
                    new_value = record[column]

                    # Update only attributes whose values differ.
                    # Example:
                    # "Comp Programming" -> "Computer Programming"
                    if old_value != new_value:
                        setattr(registration, column, new_value)
                        record_changed = True

                # Count a modified record once, even if several fields changed.
                if record_changed:
                    updated_count += 1
                else:
                    unchanged_count += 1

            # Send pending INSERT and UPDATE statements to SQL Server.
            # The transaction has not committed yet.
            session.flush()

            # Updates must not increase the number of database records.
            # Only new registration IDs should increase the count.
            database_count_after = session.scalar(
                select(func.count()).select_from(Registration)
            )

            expected_count = database_count_before + inserted_count

            if database_count_after != expected_count:
                raise RuntimeError(
                    "Import validation failed: database row count mismatch."
                )

    # Display results only after the transaction commits successfully.
    print("\nImport completed successfully.")
    print("CSV records processed:", len(records))
    print("Records inserted:", inserted_count)
    print("Records updated:", updated_count)
    print("Records unchanged:", unchanged_count)
    print("Database records before:", database_count_before)
    print("Database records after:", database_count_after)

finally:
    # Release the connection pool even if the import fails.
    project_engine.dispose()