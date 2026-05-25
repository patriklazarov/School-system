import sys
from database import DatabaseManager
from models import Student, Teacher, Course

SEPARATOR = "=" * 60


def header(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)

def info(msg: str) -> None:
    print(f"  [INFO]  {msg}")


def error(msg: str) -> None:
    print(f"  [ERROR] {msg}")


def success(msg: str) -> None:
    print(f"  [OK]    {msg}")



def prompt(label: str) -> str:
    return input(f"  {label}: ").strip()


def prompt_int(label: str) -> int:
    while True:
        try:
            return int(prompt(label))
        except ValueError:
            error("Please enter a valid integer.")


def prompt_float(label: str, lo: float, hi: float) -> float:
    while True:
        try:
            val = float(prompt(label))
            if lo <= val <= hi:
                return val
            error(f"Value must be between {lo} and {hi}.")
        except ValueError:
            error("Please enter a valid number.")

def add_student(db: DatabaseManager) -> None:
    header("Add New Student")
    name = prompt("Full name")
    fn   = prompt("Faculty number")
    age  = prompt_int("Age")

    student = Student(name, age, fn)
    if db.add_student(student):
        success(f"Student '{name}' (FN: {fn}) added successfully.")
    else:
        error(f"Faculty number '{fn}' already exists in the database.")


def display_students(db: DatabaseManager) -> None:
    header("All Students")
    students = db.get_all_students()

    if not students:
        info("No students found.")
        return

    print(f"  {'#':<4} {'Name':<25} {'FN':<12} {'Age':<5} {'Avg Grade':<12} Status")
    print(f"  {'-'*4} {'-'*25} {'-'*12} {'-'*5} {'-'*12} {'-'*10}")

    for idx, s in enumerate(students, start=1):
        avg   = s.average_grade()
        avg_s = f"{avg:.2f}" if avg is not None else "N/A"
        
        # Conditional: pass / fail / no grades
        if s.passed() is None:
            status = "No grades"
        elif s.passed():
            status = "Passed"
        else:
            status = "Failed "

        print(f"  {idx:<4} {s.name:<25} {s.faculty_number:<12} {s.age:<5} {avg_s:<12} {status}")

    print(f"\n  Total students: {len(students)}")


def add_course(db: DatabaseManager) -> None:
    header("Add New Course")
    name    = prompt("Course name")
    teacher = prompt("Teacher name (leave blank for TBA)")
    teacher = teacher if teacher else "TBA"

    course = db.add_course(name, teacher)
    if course:
        success(f"Course '{name}' (ID: {course.course_id}) created.")
    else:
        error(f"A course named '{name}' already exists.")


def display_courses(db: DatabaseManager) -> None:
    header("All Courses")
    courses = db.get_all_courses()

    if not courses:
        info("No courses found.")
        return

    print(f"  {'ID':<6} {'Course Name':<30} {'Teacher':<20} {'Enrolled'}")
    print(f"  {'-'*6} {'-'*30} {'-'*20} {'-'*8}")

    for c in courses:
        print(f"  {c.course_id:<6} {c.name:<30} {c.teacher_name:<20} {len(c.enrolled_students())}")

    print(f"\n  Total courses: {len(courses)}")


def enroll_student_in_course(db: DatabaseManager) -> None:
    header("Enroll Student in Course")
    fn        = prompt("Student faculty number")
    course_id = prompt_int("Course ID (see course list)")

    if db.enroll_student(fn, course_id):
        success(f"Student {fn} enrolled in course {course_id}.")
    else:
        error("Enrollment failed – student or course not found, or already enrolled.")


def assign_grade(db: DatabaseManager) -> None:
    header("Assign Grade to Student")
    fn        = prompt("Student faculty number")
    course_id = prompt_int("Course ID")
    grade     = prompt_float("Grade (2.00 – 6.0011)", 2.0, 6.0)

    if db.assign_grade(fn, course_id, grade):
        avg = db.get_average_grade(fn)
        success(f"Grade {grade:.2f} recorded.")
        if avg is not None:
            # Conditional: pass / fail based on average
            status = "PASSED ✓" if avg >= 3.0 else "FAILED ✗"
            info(f"New average for FN {fn}: {avg:.2f}  →  {status}")
    else:
        error("Could not assign grade. Check faculty number and course ID.")


def view_student_grades(db: DatabaseManager) -> None:
    header("View Student Grades")
    fn     = prompt("Student faculty number")
    grades = db.get_grades_for_student(fn)

    if not grades:
        info(f"No grades found for FN {fn}.")
        return

    print(f"\n  Grades for student {fn}:")
    print(f"  {'Course':<30} Grade   Status")
    print(f"  {'-'*30} {'-'*7} {'-'*10}")


    for entry in grades:
        g      = entry["grade"]
        status = "Passed ✓" if g >= 3.0 else "Failed ✗"
        print(f"  {entry['course']:<30} {g:<7.2f} {status}")

    avg = db.get_average_grade(fn)
    if avg is not None:
        overall = "PASSED ✓" if avg >= 3.0 else "FAILED ✗"
        print(f"\n  Overall average: {avg:.2f}  →  {overall}")


def search_students(db: DatabaseManager) -> None:
    header("Search Students")
    query    = prompt("Search by name or faculty number")
    students = db.search_students(query)

    if not students:
        info(f"No students found matching '{query}'.")
        return

    print(f"\n  Found {len(students)} result(s):")
    for s in students:
        avg   = s.average_grade()
        avg_s = f"{avg:.2f}" if avg is not None else "N/A"
        print(f"    • {s.name}  |  FN: {s.faculty_number}  |  Age: {s.age}  |  Avg: {avg_s}")


def delete_student(db: DatabaseManager) -> None:
    header("Delete Student")
    fn = prompt("Faculty number of student to delete")
    confirm = prompt(f"Are you sure you want to delete student {fn}? (yes/no)")
    if confirm.lower() == "yes":
        if db.delete_student(fn):
            success(f"Student {fn} deleted.")
        else:
            error(f"No student found with FN {fn}.")
    else:
        info("Deletion cancelled.")


def delete_course(db: DatabaseManager) -> None:
    header("Delete Course")
    course_id = prompt_int("Course ID to delete")
    confirm   = prompt(f"Are you sure you want to delete course {course_id}? (yes/no)")
    if confirm.lower() == "yes":
        if db.delete_course(course_id):
            success(f"Course {course_id} deleted.")
        else:
            error(f"No course found with ID {course_id}.")
    else:
        info("Deletion cancelled.")


def show_teacher_example() -> None:

    header("Teacher Class Demo (OOP Inheritance)")
    t = Teacher("Dr. Ivan Petrov", 45, "Algorithms")
    print(f"  Created: {t}")
    print(f"  Name   : {t.name}")
    print(f"  Age    : {t.age}")
    print(f"  Subject: {t.subject}")
    info("Teacher inherits name & age from Person; adds subject.")


MENU = """
  ┌─────────────────────────────────────────────┐
  │   STUDENT COURSE MANAGEMENT SYSTEM          │
  ├─────────────────────────────────────────────┤
  │  1.  Add Student                            │
  │  2.  Display All Students                   │
  │  3.  Search Students                        │
  │  4.  Delete Student                         │
  │  ─────────────────────────────────────────  │
  │  5.  Add Course                             │
  │  6.  Display All Courses                    │
  │  7.  Delete Course                          │
  │  ─────────────────────────────────────────  │
  │  8.  Enroll Student in Course               │
  │  9.  Assign Grade                           │
  │  10. View Student Grades                    │
  │  ─────────────────────────────────────────  │
  │  11. Teacher Class Demo (OOP)               │
  │  0.  Exit                                   │
  └─────────────────────────────────────────────┘
"""


def main() -> None:
    db = DatabaseManager("school.db")
    print("\n  Welcome to the Student Course Management System")
    print("  Powered by Python + SQLite\n")

    while True:
        print(MENU)
        choice = prompt("Enter your choice").strip()

        if choice == "1":
            add_student(db)
        elif choice == "2":
            display_students(db)
        elif choice == "3":
            search_students(db)
        elif choice == "4":
            delete_student(db)
        elif choice == "5":
            add_course(db)
        elif choice == "6":
            display_courses(db)
        elif choice == "7":
            delete_course(db)
        elif choice == "8":
            enroll_student_in_course(db)
        elif choice == "9":
            assign_grade(db)
        elif choice == "10":
            view_student_grades(db)
        elif choice == "11":
            show_teacher_example()
        elif choice == "0":
            db.close()
            sys.exit(0)
        else:
            error("Invalid choice. Please enter a number from the menu.")


if __name__ == "__main__":
    main()
