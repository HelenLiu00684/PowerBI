# Student Course Analytics with Power BI

A personal learning project that takes synthetic student registration data from a CSV file through cleaning, database storage, and interactive analysis.

**Workflow:** CSV → pandas → SQL Server in Docker → Power BI

## Project Overview

The dataset contains 4,862 course registration records. Each row represents one student's registration for one course. A student can therefore appear in multiple records.

The project explores four questions:

1. How does student course load relate to completion and withdrawal rates?
2. How do students from different programs perform in shared foundation courses?
3. How does course enrollment vary across terms?
4. How do students progress from prerequisite courses to subsequent courses?

All data is synthetic and used for learning purposes. The results do not represent a real educational institution.

## Tools

| Tool | Purpose |
|---|---|
| Python and pandas | Data cleaning, validation, and review exports |
| SQL Server | Storage and SQL queries |
| Docker | Local SQL Server environment |
| Power BI | Data modeling, DAX calculations, and visualization |

## Data Preparation

The pandas cleaning process includes:

- Checking required columns.
- Removing extra whitespace and standardizing identifiers.
- Mapping recognized status, program, and course labels to consistent names.
- Converting dates and identifying invalid values.
- Restoring missing course names using a confirmed course catalog.
- Restoring missing programs only when a student's records contain one consistent, approved program.
- Recording unresolved issues and conflicting values for review.

DataFrames hold the registration table, while Series and Boolean masks support column operations and row selection.

Uncertain values are preserved or flagged rather than guessed. The source CSV is not overwritten.

## Database

The prepared data is loaded into SQL Server running in a Docker container.

- Database: `CourseAnalytics`
- Table: `dbo.Registrations`

Docker runs the database environment; SQL Server stores the data.

A Docker container is not included in this repository. To reproduce the workflow, set up a SQL Server instance and configure the connection used by `database_import.py`.

## Power BI Analysis

### 1. Student Workload and Outcomes

A calculated table, `StudentTermWorkload`, groups registrations by:

- Program
- Term
- StudentID

This supports comparisons between course load and completion or withdrawal rates.

### 2. Shared Foundation Courses

The report compares outcomes across programs for shared courses, such as Java Programming.

Measures distinguish registration counts from distinct student counts.

### 3. Course Demand by Term

A matrix displays course registration counts across terms.

A Power Query sorting column places terms in chronological order:
Winter → Summer → Fall within each year.

### 4. Learning Pathways

The report links records using StudentID and course dates to examine:

- Mathematics completion before Statistics begins.
- Progression to Python Data Analysis after completing Statistics.

Calculated columns identify qualifying prior or subsequent courses. Measures summarize student counts and progression rates.

## Calculation Rules

- **Registration count:** the number of registration records.
- **Student count:** distinct, non-blank StudentIDs.
- **Eligible outcomes:** ended courses with a known final status of Completed, Not Completed, or Withdrawn.
- **Analysis cutoff:** November 17, 2026.

For progression from Statistics to Python Data Analysis, the same student must have completed Statistics and have a subsequent Data Analysis course start date on or before the analysis cutoff.

Course start dates indicate scheduled starts; the dataset does not establish actual attendance.

## Repository Structure

```text
.
├── data/                           # Synthetic source data
├── output/                         # Prepared data and review outputs
├── inspect_data.py                 # Data cleaning and validation
├── database_import.py              # SQL Server data import
├── Student_BI_2026_11_17.pbix        # Power BI report
├── .gitignore
└── README.md
```

## Running the Project

1. Create a Python environment and install the packages imported by the scripts.
2. Review the input and output paths in `inspect_data.py`.
3. Run the cleaning script:

   ```bash
   python inspect_data.py
   ```

4. Review flagged records before using the prepared data.
5. Start SQL Server and configure the database connection.
6. Run the import script:

   ```bash
   python database_import.py
   ```

7. Open `Student_BI_2026_11_17.pbix` in Power BI Desktop.
8. Update the SQL Server data source settings and credentials for your environment, then refresh the report.

Keep real passwords and local credentials outside version control.

## Limitations

- The dataset is synthetic, so findings demonstrate analytical methods rather than real-world trends.
- Program recovery assumes each student belongs to one program in this demo.
- Missing or conflicting records can limit the analysis.
- Students have different amounts of follow-up time before the analysis cutoff.
- Relationships between workload, preparation, and outcomes do not establish causation.

## What I Learned

This project strengthened my understanding of pandas DataFrames and Series, SQL Server storage, and Power BI measures, calculated columns, and calculated tables.

It also reinforced the importance of clear business rules: reliable analysis depends on understanding what each record and metric actually represents.
