import sqlite3
from typing import Optional
from models import Student, Course


class DatabaseManager:

    def __init__(self, db_path: str = "school.db"):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    # ------------------------------------------------------------------ #
    #  Connection helpers                                                   #
    # ------------------------------------------------------------------ #

    def _connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row          # access columns by name
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    # ------------------------------------------------------------------ #
    #  Schema creation                                                      #
    # ------------------------------------------------------------------ #

    def _create_tables(self) -> None:
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS students (
                faculty_number TEXT PRIMARY KEY,
                name           TEXT NOT NULL,
                age            INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS courses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL UNIQUE,
                teacher_name TEXT NOT NULL DEFAULT 'TBA'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS grades (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_number TEXT NOT NULL,
                course_id      INTEGER NOT NULL,
                grade          REAL NOT NULL,
                FOREIGN KEY (faculty_number) REFERENCES students(faculty_number),
                FOREIGN KEY (course_id)      REFERENCES courses(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                faculty_number TEXT NOT NULL,
                course_id      INTEGER NOT NULL,
                PRIMARY KEY (faculty_number, course_id),
                FOREIGN KEY (faculty_number) REFERENCES students(faculty_number),
                FOREIGN KEY (course_id)      REFERENCES courses(id)
            )
            """,
        ]
        for stmt in sql_statements:
            self._conn.execute(stmt)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    #  Student operations                                                   #
    # ------------------------------------------------------------------ #

    def add_student(self, student: Student) -> bool:
        """INSERT a student. Returns False if faculty number already exists."""
        try:
            self._conn.execute(
                "INSERT INTO students (faculty_number, name, age) VALUES (?, ?, ?)",
                (student.faculty_number, student.name, student.age),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_students(self) -> list[Student]:
        """SELECT all students and reconstruct Student objects with their grades."""
        rows = self._conn.execute(
            "SELECT faculty_number, name, age FROM students ORDER BY name"
        ).fetchall()

        students: list[Student] = []
        for row in rows:
            s = Student(row["name"], row["age"], row["faculty_number"])
            # Load grades into the in-memory list
            grade_rows = self._conn.execute(
                "SELECT grade FROM grades WHERE faculty_number = ?",
                (row["faculty_number"],),
            ).fetchall()
            for g in grade_rows:
                s.add_grade(g["grade"])
            students.append(s)
        return students

    def search_students(self, query: str) -> list[Student]:
        """Search students by name (partial, case-insensitive) or faculty number."""
        like_query = f"%{query}%"
        rows = self._conn.execute(
            """
            SELECT faculty_number, name, age FROM students
            WHERE LOWER(name) LIKE LOWER(?) OR faculty_number LIKE ?
            ORDER BY name
            """,
            (like_query, like_query),
        ).fetchall()

        students: list[Student] = []
        for row in rows:
            s = Student(row["name"], row["age"], row["faculty_number"])
            grade_rows = self._conn.execute(
                "SELECT grade FROM grades WHERE faculty_number = ?",
                (row["faculty_number"],),
            ).fetchall()
            for g in grade_rows:
                s.add_grade(g["grade"])
            students.append(s)
        return students

    def delete_student(self, faculty_number: str) -> bool:
        """DELETE a student and all related records."""
        cursor = self._conn.execute(
            "DELETE FROM students WHERE faculty_number = ?", (faculty_number,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Course operations                                                    #
    # ------------------------------------------------------------------ #

    def add_course(self, name: str, teacher_name: str = "TBA") -> Optional[Course]:
        """INSERT a course. Returns the new Course or None if name already exists."""
        try:
            cursor = self._conn.execute(
                "INSERT INTO courses (name, teacher_name) VALUES (?, ?)",
                (name, teacher_name),
            )
            self._conn.commit()
            return Course(cursor.lastrowid, name, teacher_name)
        except sqlite3.IntegrityError:
            return None

    def get_all_courses(self) -> list[Course]:
        """SELECT all courses."""
        rows = self._conn.execute(
            "SELECT id, name, teacher_name FROM courses ORDER BY name"
        ).fetchall()
        courses = []
        for row in rows:
            c = Course(row["id"], row["name"], row["teacher_name"])
            # Load enrolled students
            enr_rows = self._conn.execute(
                "SELECT faculty_number FROM enrollments WHERE course_id = ?",
                (row["id"],),
            ).fetchall()
            for e in enr_rows:
                c.enroll(e["faculty_number"])
            courses.append(c)
        return courses

    def get_course_by_id(self, course_id: int) -> Optional[Course]:
        row = self._conn.execute(
            "SELECT id, name, teacher_name FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        if row is None:
            return None
        return Course(row["id"], row["name"], row["teacher_name"])

    def delete_course(self, course_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM courses WHERE id = ?", (course_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Enrollment operations                                                #
    # ------------------------------------------------------------------ #

    def enroll_student(self, faculty_number: str, course_id: int) -> bool:
        """Enroll a student in a course (INSERT into enrollments)."""
        try:
            self._conn.execute(
                "INSERT INTO enrollments (faculty_number, course_id) VALUES (?, ?)",
                (faculty_number, course_id),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False   # already enrolled

    # ------------------------------------------------------------------ #
    #  Grade operations                                                     #
    # ------------------------------------------------------------------ #

    def assign_grade(
        self, faculty_number: str, course_id: int, grade: float
    ) -> bool:
        """
        INSERT or UPDATE a grade for a student in a course.
        A student can only have one grade per course (UPDATE replaces it).
        """
        existing = self._conn.execute(
            "SELECT id FROM grades WHERE faculty_number = ? AND course_id = ?",
            (faculty_number, course_id),
        ).fetchone()

        if existing:
            self._conn.execute(
                "UPDATE grades SET grade = ? WHERE id = ?",
                (grade, existing["id"]),
            )
        else:
            self._conn.execute(
                "INSERT INTO grades (faculty_number, course_id, grade) VALUES (?, ?, ?)",
                (faculty_number, course_id, grade),
            )
        self._conn.commit()
        return True

    def get_grades_for_student(self, faculty_number: str) -> list[dict]:
        """Return all grade records for a specific student."""
        rows = self._conn.execute(
            """
            SELECT c.name AS course_name, g.grade
            FROM grades g
            JOIN courses c ON g.course_id = c.id
            WHERE g.faculty_number = ?
            ORDER BY c.name
            """,
            (faculty_number,),
        ).fetchall()
        return [{"course": row["course_name"], "grade": row["grade"]} for row in rows]

    def get_average_grade(self, faculty_number: str) -> Optional[float]:
        """Compute AVG grade for a student using SQL aggregation."""
        row = self._conn.execute(
            "SELECT AVG(grade) AS avg FROM grades WHERE faculty_number = ?",
            (faculty_number,),
        ).fetchone()
        if row and row["avg"] is not None:
            return round(row["avg"], 2)
        return None
