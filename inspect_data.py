"""Prepare synthetic course registrations for SQL Server import.

Run from any directory: python3 course-analytics/inspect_data.py
Requires pandas 2.0 or newer for mixed-format date parsing.
Prerequisite eligibility checks are deferred to the database stage.
"""

"""
SERIES FUNCTIONS:
Create a pandas Series:
values = pd.Series(
    ["Python", "Statistics"],
    index=[10, 20],
    dtype="string"
)

Result:
10    Python
20    Statistics

A Series contains values and corresponding index labels.
Each example below defines its own initial Series.


1. .str.strip() removes leading and trailing whitespace.

values = pd.Series(["  Python  ", " Statistics "], dtype="string")
result = values.str.strip()

result.tolist()
Result: ["Python", "Statistics"]


2. .str.replace() replaces consecutive whitespace with one space.
Leading and trailing whitespace also becomes one space.

values = pd.Series(["  Python  Fundamentals ", "Data   Analysis"])
result = values.str.replace(r"\s+", " ", regex=True)

result.tolist()
Result: [" Python Fundamentals ", "Data Analysis"]


3. .str.lower() converts text to lowercase.

values = pd.Series(["PYTHON", "Statistics"])
result = values.str.lower()

result.tolist()
Result: ["python", "statistics"]


4. .str.upper() converts text to uppercase.

values = pd.Series(["python", "Statistics"])
result = values.str.upper()

result.tolist()
Result: ["PYTHON", "STATISTICS"]


5. .isna() identifies actual missing values.
Empty strings and the text "None" are not missing values.

values = pd.Series(["Python", pd.NA, "", "None"], dtype="string")
result = values.isna()

result.tolist()
Result: [False, True, False, False]


6. .notna() identifies values that are not missing.

values = pd.Series(["Python", pd.NA, ""], dtype="string")
result = values.notna()

result.tolist()
Result: [True, False, True]


7. .eq() compares each value with a specified value.
With string dtype, a missing value produces pd.NA.

values = pd.Series(["Python", "Statistics", pd.NA], dtype="string")
result = values.eq("Statistics")

result.tolist()
Result: [False, True, pd.NA]


8. .fillna() replaces missing values.

values = pd.Series(["Python", pd.NA, "Statistics"], dtype="string")
result = values.fillna("Unknown")

result.tolist()
Result: ["Python", "Unknown", "Statistics"]


9. .astype() converts the data type.

values = pd.Series(["10", "20", "30"], dtype="string")
result = values.astype("int64")

result.tolist()
Result: [10, 20, 30]


10. .copy() creates a separate copy.

values = pd.Series(["Python", "Statistics"], index=[10, 20])
copied_values = values.copy()
copied_values.loc[20] = "Mathematics"

copied_values.tolist()
Result: ["Python", "Mathematics"]

values.tolist()
Result: ["Python", "Statistics"]


11. .unique() returns distinct values in their order of appearance.

values = pd.Series(["Python", "Python", "Statistics"])
result = values.unique()

result.tolist()
Result: ["Python", "Statistics"]


12. .value_counts() returns a Series containing value frequencies.
Missing values are excluded by default.

values = pd.Series(["Python", "Python", "Statistics", pd.NA])
result = values.value_counts()

result.to_dict()
Result: {"Python": 2, "Statistics": 1}


13. .sum() adds numeric values.

values = pd.Series([80, 90, 70])
result = values.sum()

Result: 240


14. .sum() on a Boolean Series counts True values.

values = pd.Series(["Python", pd.NA, pd.NA], dtype="string")
missing_mask = values.isna()

missing_mask.tolist()
Result: [False, True, True]

missing_mask.sum()
Result: 2


15. .tolist() converts Series values into a Python list.
The index labels are not included.

values = pd.Series(["S0001", "S0002"], index=[10, 20])
result = values.tolist()

Result: ["S0001", "S0002"]


16. .loc selects a value by its index label.

values = pd.Series(["Python", "Statistics"], index=[10, 20])
result = values.loc[20]

Result: "Statistics"


17. .loc updates a value by its index label.

values = pd.Series(["Python", "Statistics"], index=[10, 20])
values.loc[20] = "Mathematics"

values.tolist()
Result: ["Python", "Mathematics"]


18. .loc selects entries using a Boolean Series.

values = pd.Series(
    ["Python", pd.NA, "Statistics"],
    index=[10, 20, 30],
    dtype="string"
)
missing_mask = values.isna()
result = values.loc[missing_mask]

result.index.tolist()
Result: [20]

result.tolist()
Result: [pd.NA]


19. Chain operations and assign the resulting Series.
Parentheses allow the expression to span multiple lines.

values = pd.Series(["  Python  Fundamentals ", " Data   Analysis "])
cleaned_values = (
    values.str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

cleaned_values.tolist()
Result: ["Python Fundamentals", "Data Analysis"]

values.tolist()
Result: ["  Python  Fundamentals ", " Data   Analysis "]

"""

from pathlib import Path
import pandas as pd


# 1. Define Paths and Business Rules

# Locate input and output relative to this script, not the terminal folder.
# Input:  data/SCRTotal.csv
# Output: output/registrations_prepared.csv
#         output/registrations_review.csv
project_dir = Path(__file__).resolve().parent
csv_path = project_dir / "data" / "SCRTotal.csv"
output_dir = project_dir / "output"

# Preserve the existing project rules below.
# These course labels describe our synthetic project, not a real catalog.
# Mapping keys are matched exactly after lowercase conversion.
# Example: "COMPLETED" -> "completed" -> "Completed".
# Known spelling aliases are explicit; unknown values are never guessed.

id_columns = [
    "RegistrationID",
    "StudentID",
    "CourseID",
]

status_mapping = {
    "completed": "Completed",
    "not completed": "Not Completed",
    "withdrawn": "Withdrawn",
    "registered": "Registered",
}

course_names_by_id = {
    "C001": "English for Academic Purposes",
    "C002": "Professional Communication",
    "C003": "Ethics and Digital Citizenship",
    "C004": "Mathematics for Computing",
    "C005": "Statistics",
    "C006": "Python Fundamentals",
    "C007": "Java Programming",
    "C008": "Python Data Analysis",
    "C009": "Data Structures and Algorithms",
    "C010": "Database Technology and SQL",
    "C011": "Networking Fundamentals",
    "C012": "Cloud Infrastructure",
    "C013": "Cybersecurity Fundamentals",
    "C014": "Operating Systems and IT Troubleshooting",
    "C015": "Business Requirements Analysis",
}

program_mapping = {
    "computer programming": "Computer Programming",
    "computer science": "Computer Science",
    "computer networking": "Computer Networking",
    "artificial intelligence": "Artificial Intelligence",
    "artificial inteligence": "Artificial Intelligence",
    "cloud computing": "Cloud Computing",
    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "it support and maintenance": "IT Support and Maintenance",
    "business analysis": "Business Analysis",
    "business analaysis": "Business Analysis",
    "comp programming": "Computer Programming",
    "compu science": "Computer Science",
    "artificial intelli": "Artificial Intelligence",
    "cloud compting": "Cloud Computing",
    "cloud comuting": "Cloud Computing",
    "com networking": "Computer Networking",
}

date_columns = [
    "RegistrationDate",
    "CourseStartDate",
    "CourseEndDate",
]

# Build course-name matching rules from the confirmed course catalog.
# This avoids maintaining the same fifteen labels in two dictionaries.
# Dictionary comprehension means: create one key-value pair per name.
# Example: "Python Fundamentals" becomes
#          "python fundamentals": "Python Fundamentals".
# Build a lowercase-to-standard-name lookup.

course_mapping = {
    name.lower(): name for name in course_names_by_id.values()
}

# Select the appropriate mapping by column name.
# This configuration replaces three almost identical if/elif branches.
# Example: label_mappings["Status"] returns status_mapping.
label_mappings = {
    "Status": status_mapping,
    "Program": program_mapping,
    "CourseName": course_mapping,
}

required_columns = [
    "RegistrationID", "StudentID", "Program", "CourseID", "CourseName",
    "Term", "RegistrationDate", "CourseStartDate", "CourseEndDate",
    "Status", "PrerequisiteCourses",
]


# 2. Load and Inspect the Original Data

# Explicit string dtype keeps IDs as text and supports .str operations.
# keep_default_na=False preserves text such as "None", "NA", and "NULL".
# na_values=[""] treats genuinely empty fields as missing.
# "None" means no prerequisite; a missing field means not provided.
# Other markers are not silently reinterpreted without a business rule.
df = pd.read_csv(
    csv_path,
    encoding="utf-8-sig",
    dtype="string",
    keep_default_na=False,  # Preserve literal markers such as None, NULL, and NA.
    na_values=[""],         # Treat empty fields as missing.
)
"""
Function 1:
pd.Index() creates a pandas Index from a sequence, such as a list.

.difference() returns the elements in the first Index that are absent
from the second Index. The result is also a pandas Index.

.tolist() converts a pandas Index or Series into a Python list,
preserving the values and their order. For a Series, index labels
are not included.

Example 1: Find missing required columns.
required = pd.Index(["StudentID", "CourseID", "Status"])
actual = pd.Index(["StudentID", "CourseName", "Status"])

missing_columns = required.difference(actual).tolist()
Result: ["CourseID"]

Example 2: Find additional columns in the dataset.
extra_columns = actual.difference(required).tolist()
Result: ["CourseName"]

Example 3: Convert a Series into a Python list.
student_ids = pd.Series(["S0001", "S0002"], index=[10, 20])

student_list = student_ids.tolist()
Result: ["S0001", "S0002"]

# """
# Stop with a useful message if required fields are missing.
missing_columns = pd.Index(required_columns).difference(df.columns)
if len(missing_columns):
    raise ValueError(f"Missing required columns: {missing_columns.tolist()}")

# Preserve all original parsed values before any cleaning.
# Unknown values and invalid date text remain available here for review.
raw_df = df.copy()

# Display the number of rows and columns as (rows, columns).
# Example: (4862, 11) means 4,862 registration records and 11 columns.
print("Dataset shape:", df.shape)

# Count distinct non-missing student IDs before cleaning.
# "S0754" and " S0754 " count as different IDs at this stage.
print("Unique students before cleaning:", df["StudentID"].nunique())

# Print a section title; \n adds a blank line before the title.
print("\nOriginal column types:")

# Display the data type of each column.
# dtype="string" in read_csv() initially loads every column as text.
print(df.dtypes)

# Print a title for the missing-value counts before cleaning.
print("\nMissing values before cleaning:")


"""
Function 2:
pd.read_csv(..., keep_default_na=False) preserves strings such as
"None", "NA", and "NULL" as text instead of treating them as missing
values. Empty CSV fields are also preserved as empty strings.

df.isna().sum() counts actual missing values in each column, including
Python None, pd.NA, NaN, and NaT. It does not count text such as
"None", "NA", "NULL", empty strings, or whitespace-only strings.

To count blank entries as missing while preserving meaningful text,
convert empty and whitespace-only strings to pd.NA first:

df = df.replace(r"^\s*$", pd.NA, regex=True)
print(df.isna().sum())
"""

print(df.isna().sum())

# Print a title for the original data preview.
print("\nFirst five original records:")

"""
df.head() returns a DataFrame, which has no .tolist() method.
.tolist() is available on pandas Series and Index objects.

To convert one column to a list:
df["RegistrationID"].head().tolist()

To convert all selected rows to a list of lists:
df.head().to_numpy().tolist()
Here, .to_numpy() creates a NumPy array, and the array's .tolist()
method converts it into nested Python lists. Column names and row
index labels are not included.

To print the first five rows as a table with column names:
print(df.head().to_string(index=False))
"""
print(df.head().to_string(index=False))

"""
Create a string Series with the same row index as df.
Each value starts as an empty string and stores review reasons for
the corresponding row. Using a Series supports updates with .loc
and Boolean masks while keeping reasons aligned with df by index.

Example:
review_reasons.loc[15] = "Missing StudentID"

Here, 15 is the row index label, not necessarily the row's position.
"""
review_reasons = pd.Series("", index=df.index, dtype="string")


# 3. Clean All Columns in One Loop

print("\nCleaning results by column:")
"""
Process each column through five stages:
1. Copy the original column.
2. Normalize whitespace and blank values.
3. Apply rules specific to the column type.
4. Report changes or date-parsing results.
5. Assign the processed Series back to df.

Status, Program, and CourseName use dictionary mapping.
Identifiers, prerequisites, and dates have separate processing rules.

Assumptions:
- Input columns contain text or missing values and support .str.
- Column names are unique.
- Mapping dictionary keys are lowercase.
- The column categories do not overlap.
- review_reasons is a string Series initialized with empty strings
  and the same row index as df.
"""
for column in df.columns:
    """
    df.columns is an iterable pandas Index of column names.
    Each iteration assigns one column name to column.

    df[column] selects the current column as a Series.
    .copy() preserves its original values for comparison later.

    Example:
    column = "Status"
    original_values = df["Status"].copy()
    """
    original_values = df[column].copy()

    r"""
    Normalize whitespace across the current column.
    .str.strip() removes leading and trailing whitespace.
    .str.replace() replaces consecutive whitespace with one space.
    In the regular expression, \s means whitespace and + means
    one or more occurrences.

    Example:
    "  Python  Fundamentals " -> "Python Fundamentals"

    Each operation returns a Series with the same index.
    Parentheses allow the expression to span multiple lines.
    Existing missing values remain missing.
    """
    values = (
        original_values.str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    """
    Convert empty strings to actual missing values.
    Whitespace-only fields became empty during the previous step.

    Examples:
    "   " -> "" -> pd.NA
    "" -> pd.NA
    "None" -> "None"

    Literal text such as "None", "NA", and "NULL" remains text
    if it was preserved when loading the data.
    """
    values = values.replace("", pd.NA)

    if column in id_columns:
        """
        Standardize identifier columns by converting text to uppercase.
        Leading and trailing whitespace has already been removed.

        Example:
        " c006 " -> "c006" -> "C006"

        This changes formatting without checking whether the identifier
        exists in an authoritative list.
        """
        values = values.str.upper()

    elif column in label_mappings:
        """
        Select one of three mapping dictionaries based on column.

        | Current column | Selected dictionary |
        |----------------|---------------------|
        | "Status"       | status_mapping      |
        | "Program"      | program_mapping     |
        | "CourseName"   | course_mapping      |

        mapping refers to the dictionary selected for this iteration.
        All three columns share the same processing steps.

        Example:
        When column is "Status":
        mapping = label_mappings["Status"]

        This selects status_mapping, such as:
        {
            "completed": "Completed",
            "registered": "Registered",
            "withdrawn": "Withdrawn",
            "not completed": "Not Completed",
        }
        """
        mapping = label_mappings[column]
        print(mapping)

        """
        Create lowercase lookup keys while keeping values unchanged.
        keys is a Series with the same index as values.

        Example:
        values: ["COMPLETED", "Unknown", "registered", pd.NA]
        keys:   ["completed", "unknown", "registered", pd.NA]
        """
        keys = values.str.lower()

        """
        Check whether each key exists in the selected dictionary.
        recognized_mask is a Boolean Series.

        Assuming the dictionary recognizes completed and registered:
        keys:            ["completed", "unknown", "registered", pd.NA]
        recognized_mask: [True, False, True, False]
        """
        recognized_mask = keys.isin(mapping.keys())

        """
        Select values that are present but not recognized by the mapping.

        values.notna() is True when a value is not missing.
        ~recognized_mask is True when a value is not recognized.
        & requires both conditions to be True.

        Example:
        values = pd.Series(
            ["COMPLETED", "Unknown", "registered", pd.NA],
            dtype="string"
        )

        recognized_mask:
        [True, False, True, False]

        values.notna():
        [True, True, True, False]

        ~recognized_mask:
        [False, True, False, True]

        | Index | Value        | Not missing | Unrecognized | Selected |
        |-------|--------------|-------------|--------------|----------|
        | 0     | "COMPLETED"  | True        | False        | False    |
        | 1     | "Unknown"    | True        | True         | True     |
        | 2     | "registered" | True        | False        | False    |
        | 3     | pd.NA        | False       | True         | False    |

        The resulting unexpected_mask contains:
        [False, True, False, False]

        Applying the mask selects the actual values:
        values.loc[unexpected_mask].tolist()
        Result: ["Unknown"]

        Only "Unknown" at index 1 is selected for review.
        Missing values are excluded from this particular check.
        """
        unexpected_mask = values.notna() & ~recognized_mask

        if unexpected_mask.any():
            """
            .any() returns True if at least one row is flagged.
            Print unexpected labels and their occurrence counts.

            For the example above:
            Unknown    1
            """
            print(f"\nUnexpected labels in {column}:")
            print(values.loc[unexpected_mask].value_counts())

            """
            Append a review reason to each flagged row.
            .loc selects rows using the Boolean mask.
            Matching index labels keep reasons aligned with df.
            += preserves reasons recorded for earlier columns.

            For the example above, when column is "Status":
            review_reasons.loc[1] receives:
            "Unrecognized Status: Unknown; "
            """
            review_reasons.loc[unexpected_mask] += (
                "Unrecognized " + column + ": "
                + values.loc[unexpected_mask] + "; "
            )

        """
        Map recognized keys to their standard labels.

        Right side:
        keys.loc[recognized_mask] selects recognized lookup keys.
        .map(mapping) uses each selected key to find its standard label.
        The result is a Series retaining the selected index labels.
        Each key is in the series of keys.

        Left side:
        values.loc[recognized_mask] selects the rows to update.
        Assignment aligns the mapped results by index.

        | Index | Original value | Recognized | Final value  |
        |-------|----------------|------------|--------------|
        | 0     | "COMPLETED"    | True       | "Completed"  |
        | 1     | "Unknown"      | False      | "Unknown"    |
        | 2     | "registered"   | True       | "Registered" |
        | 3     | pd.NA          | False      | pd.NA        |

        Unrecognized labels retain their whitespace-normalized text.
        Missing values remain missing.
        """
        values.loc[recognized_mask] = keys.loc[recognized_mask].map(mapping)

    elif column == "PrerequisiteCourses":
        """
        Standardize the marker meaning no prerequisite is required.

        Examples after whitespace normalization:
        "None" -> "None"
        "none" -> "None"
        pd.NA -> pd.NA

        .eq("none") compares each lowercase value with "none".
        .fillna(False) makes missing comparison results False.

        Other prerequisite declarations are preserved.
        Checking their correctness requires separate business validation.
        """
        no_prerequisite_mask = values.str.lower().eq("none").fillna(False)
        values.loc[no_prerequisite_mask] = "None"

    elif column in date_columns:
        """
        Convert date text into pandas datetime values.
        format="mixed" infers a format for each value.
        errors="coerce" converts invalid input to NaT.
        Originally missing input also becomes NaT.

        Examples:
        "2025-01-13"          -> a datetime value
        "2025/01/13"          -> a datetime value
        "2025-01-13 00:00:00" -> a datetime value
        "2025-02-30"          -> NaT
        pd.NA                -> NaT

        This call does not explicitly set a day-first convention.
        Confirm the source convention for ambiguous dates.
        For day/month/year input, add dayfirst=True.
        """
        parsed_dates = pd.to_datetime(
            values,
            format="mixed",
            errors="coerce"
        )

        """
        Distinguish invalid date text from originally missing input.

        values.notna(): the input was present.
        parsed_dates.isna(): parsing produced a missing date.
        Both must be True to flag a conversion failure.

        | Input        | Parsed result | Invalid date |
        |--------------|---------------|--------------|
        | "2025-01-13" | Valid date    | False        |
        | "2025-02-30" | NaT           | True         |
        | pd.NA        | NaT           | False        |
        """
        invalid_date_mask = values.notna() & parsed_dates.isna()

        if invalid_date_mask.any():
            """
            Display invalid date text and record it for manual review.
            values still contains the input text at this point,
            allowing the invalid text to be recorded before replacement.
            """
            print(f"\nInvalid dates in {column}:")
            print(values.loc[invalid_date_mask].to_string())

            review_reasons.loc[invalid_date_mask] += (
                "Invalid " + column + ": "
                + values.loc[invalid_date_mask] + "; "
            )

        """
        Use the parsed datetime Series as the processed column.
        Its row index remains aligned with df.
        """
        values = parsed_dates

    """
    Report dates and text using different counts.
    Successful date conversion changes data types as expected,
    so it is reported separately from text corrections.
    """
    if column in date_columns:
        """
        .notna().sum() counts successfully parsed dates.
        invalid_date_mask.sum() counts conversion failures.
        Originally missing dates are excluded from both counts.
        """
        print(
            f"{column}: {values.notna().sum()} dates parsed; "
            f"{invalid_date_mask.sum()} invalid dates"
        )
    else:
        """
        Compare original and processed text values.

        The first condition compares content, temporarily replacing
        missing values with empty strings for comparison.

        The second condition compares missing-value status.
        This detects changes such as an empty string becoming pd.NA.

        | Original | Processed   | Changed |
        |----------|-------------|---------|
        | " c006 " | "C006"      | True    |
        | ""       | pd.NA       | True    |
        | pd.NA    | pd.NA       | False   |
        | "Python" | "Python"    | False   |

        .ne() means not equal.
        | combines the two conditions using element-wise OR.
        .sum() counts True values in the resulting Boolean Series.

        These counts describe changed cells, not necessarily errors.
        """
        changed_mask = (
            original_values.fillna("").ne(values.fillna(""))
            | original_values.isna().ne(values.isna())
        )
        print(f"{column}: {changed_mask.sum()} records changed")

    """
    Assign the processed Series back to the current DataFrame column.
    Values align with df by their row index labels.

    This updates df in memory. Writing a CSV or Excel file requires
    a separate export operation.
    """
    df[column] = values

"""
4. Restore Missing Course Names from the Confirmed Catalog

Use CourseID to look up the official course name in course_names_by_id.
Fill only missing CourseName values. Existing names remain unchanged.

Example catalog:
course_names_by_id = {
    "C004": "Mathematics for Computing",
    "C005": "Statistics",
}

| Index | CourseID | Existing CourseName | Candidate name           | Final CourseName         |
|-------|----------|---------------------|--------------------------|--------------------------|
| 0     | C004     | Missing             | Mathematics for Computing| Mathematics for Computing|
| 1     | C005     | Statistics          | Statistics               | Statistics               |
| 2     | C999     | Missing             | Missing                  | Missing                  |

C999 is absent from the catalog, so its missing name remains unresolved.
"""

"""
Count missing course names before recovery.
.isna() produces a Boolean Series, and .sum() counts True values.
"""
missing_courses_before = df["CourseName"].isna().sum()

"""
Create one candidate name per registration using its CourseID.
.map() looks up each ID in the catalog dictionary.
The resulting Series keeps the same row index as df.
"""
candidate_names = df["CourseID"].map(course_names_by_id)

"""
Fill missing names using candidates with matching row index labels.
If a candidate is also missing, the course name stays missing.
Existing names are preserved for separate validation.
"""
df["CourseName"] = df["CourseName"].fillna(candidate_names)

"""
Calculate how many missing names were successfully restored.

Example:
4 missing before - 1 missing afterward = 3 restored.
"""
courses_restored = missing_courses_before - df["CourseName"].isna().sum()
print("\nMissing course names restored:", courses_restored)


"""
5. Restore Missing Programs from Consistent Student Records

Business assumption for this demo:
A student belongs to one program across their registration records.

Use a student's existing records to recover a missing Program only when:
- StudentID is present.
- Exactly one distinct non-missing program is recorded for that student.
- That program is an approved value in program_mapping.

Run this after column normalization so IDs and program names are
standardized before comparing records.

Example input:
| Index | StudentID | Program              |
|-------|-----------|----------------------|
| 0     | S0001     | Computer Science     |
| 1     | S0001     | Missing              |
| 2     | S0002     | Computer Programming |
| 3     | S0002     | Business Analysis    |
| 4     | S0002     | Missing              |
| 5     | S0003     | Missing              |
"""

missing_programs_before = df["Program"].isna().sum()

"""
Group registrations by StudentID and count distinct non-missing programs.
.nunique() excludes missing program values by default.
.groupby() excludes missing StudentID groups by default.

For the example above:
| StudentID | Distinct non-missing programs |
|-----------|-------------------------------|
| S0001     | 1                             |
| S0002     | 2                             |
| S0003     | 0                             |

A count of 1 provides an unambiguous candidate.
A count above 1 indicates conflicting records under the demo assumption.
A count of 0 provides no candidate for recovery.
"""
program_counts = df.groupby("StudentID")["Program"].nunique()

"""
Select students with exactly one distinct non-missing program.
The comparison creates a Boolean Series.
.index extracts the StudentID labels of the selected entries.

For the example:
safe_student_ids contains S0001.
"""
safe_student_ids = program_counts[program_counts == 1].index

"""
Select registrations belonging to those students and build a lookup Series.
.groupby("StudentID") groups their records.
.first() returns the first non-missing Program in each group.

Because each selected student has only one distinct non-missing program,
the selected value is unambiguous.

For the example:
student_programs has StudentID as its index and Program as its value:

StudentID
S0001    Computer Science
"""
student_programs = (
    df.loc[df["StudentID"].isin(safe_student_ids)]
    .groupby("StudentID")["Program"].first()
)

"""
Keep candidate programs that appear in the approved standard labels.
program_mapping.values() supplies those labels.

Example:
"Computer Science" is retained if approved.
An unfamiliar program name is excluded from the recovery lookup,
even if it is the student's only recorded program.
"""
student_programs = student_programs.loc[
    student_programs.isin(program_mapping.values())
]

"""
Create a candidate program for each registration.

When .map() receives a Series:
- The lookup Series index supplies the matching keys, here StudentID.
- The lookup Series values supply the results, here Program.

For the example:
S0001 -> Computer Science
S0002 -> Missing, because its records conflict.
S0003 -> Missing, because no program is known.
"""
candidate_programs = df["StudentID"].map(student_programs)

"""
Fill only missing Program values, aligning candidates by row index.

For the example:
- Index 1 is filled with Computer Science.
- Index 4 remains missing because S0002 has conflicting programs.
- Index 5 remains missing because S0003 has no known program.
- Existing Program values remain unchanged.
"""
df["Program"] = df["Program"].fillna(candidate_programs)

"""
Count successful recoveries by comparing missing-value totals.
"""
programs_restored = missing_programs_before - df["Program"].isna().sum()
print("Missing programs restored:", programs_restored)

"""
Identify students with more than one distinct non-missing program.
Flag all their registration rows so the records can be reviewed together.

For the example:
conflicting_ids contains S0002.
conflict_mask selects row index labels 2, 3, and 4.

Append a review reason to each selected row without choosing a program.
"""
conflicting_ids = program_counts[program_counts > 1].index
conflict_mask = df["StudentID"].isin(conflicting_ids)
review_reasons.loc[conflict_mask] += "Conflicting programs for StudentID; "
# 6. Assemble Review Records and Check Basic Export Requirements

# Preserve registrations with unresolved missing information.
# axis=1 checks across the fields in EACH ROW.
# This is reporting after recovery, not another field-cleaning pass.
missing_fields = pd.Series("", index=df.index, dtype="string")
for column in df.columns:
    field_missing_mask = df[column].isna()
    missing_fields.loc[field_missing_mask] += column + "; "

missing_fields = missing_fields.str.rstrip("; ")
review_reasons = review_reasons.str.rstrip("; ")

# Include missing fields AND previously recorded unknown/invalid values.
# A record with multiple issues is exported once with its descriptions.
review_mask = missing_fields.ne("") | review_reasons.ne("")
review_records = df.loc[review_mask].copy()
review_records["MissingFields"] = missing_fields.loc[review_mask]
review_records["ReviewReasons"] = review_reasons.loc[review_mask]

# Stop before export if registration identity or row preservation fails.
if df.shape != raw_df.shape:
    raise ValueError("The dataset shape changed unexpectedly.")
if df["RegistrationID"].isna().any():
    raise ValueError("RegistrationID must not be missing before export.")
if not df["RegistrationID"].is_unique:
    raise ValueError("RegistrationID must be unique before export.")


# 7. Summarize Results Before Export

# Missing counts are EXPECTED to change after evidence-based recovery.
# Display before/after counts instead of an ambiguous unchanged flag.
missing_summary = pd.DataFrame({
    "Before": raw_df.isna().sum(),
    "After": df.isna().sum(),
})
print("\nMissing-value summary:")
print(missing_summary.to_string())
print("\nPrepared dataset shape:", df.shape)
print("Unique identified students:", df["StudentID"].nunique())
print("Registrations requiring review:", len(review_records))
print("\nDate column types:")
print(df[date_columns].dtypes)
print("\nStatus registration counts:")
print(df["Status"].value_counts(dropna=False))
print("\nProgram registration counts:")
print(df["Program"].value_counts(dropna=False))
print("\nCourse registration counts:")
print(df["CourseName"].value_counts(dropna=False))
print("\nFirst five prepared records:")
print(df.head().to_string(index=False))


# 8. Export All Registrations and a Separate Review List

# Every registration stays in the prepared dataset, including review rows.
# Remaining unknown student IDs, statuses, and dates are not guessed.
# These outputs are suitable for staging; unresolved records need review
# before analyses that depend on the missing or unvalidated fields.
output_dir.mkdir(parents=True, exist_ok=True)
prepared_path = output_dir / "registrations_prepared.csv"
review_path = output_dir / "registrations_review.csv"

# index=False excludes the pandas row index from each CSV.
# date_format writes dates as YYYY-MM-DD.
# na_rep="" exports missing values as empty fields.
# Literal "None" remains text, separate from an empty prerequisite field.
df.to_csv(
    prepared_path, index=False, encoding="utf-8-sig",
    date_format="%Y-%m-%d", na_rep="",
)
review_records.to_csv(
    review_path, index=False, encoding="utf-8-sig",
    date_format="%Y-%m-%d", na_rep="",
)
print("\nExport completed:")
print("Prepared dataset:", prepared_path)
print("Review records:", review_path)

# Deferred to SQL validation:
# - CourseID-to-CourseName conflicts in existing non-missing values
# - Date sequence and same-student/course/term duplicate checks
# - Incorrect or incomplete prerequisite declarations
# - Each student's prerequisite completion history
# Reload exported CSVs with the same explicit missing-value rules.
