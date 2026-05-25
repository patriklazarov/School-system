class Person:
    def __init__(self, name: str, age: int):
        self._name = name
        self._age = age

    @property
    def name(self) -> str:
        return self._name

    @property
    def age(self) -> int:
        return self._age

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name}, age={self._age})"
class Student(Person):
    def __init__(self, name: str, age: int, faculty_number: str):
        super().__init__(name, age)
        self._faculty_number = faculty_number
        self._grades: list[float] = []   # in-memory cache; DB is the source of truth

    @property
    def faculty_number(self) -> str:
        return self._faculty_number

    @property
    def grades(self) -> list[float]:
        return list(self._grades)

    def add_grade(self, grade: float) -> None:
        """Add a grade to the in-memory list (use DatabaseManager to persist)."""
        if not (2.0 <= grade <= 6.0):
            raise ValueError("Grade must be between 2.00 and 6.00 (Bulgarian scale).")
        self._grades.append(grade)

    def average_grade(self) -> float | None:
        """Return the average of all in-memory grades, or None if no grades."""
        if not self._grades:
            return None
        return round(sum(self._grades) / len(self._grades), 2)

    def passed(self) -> bool | None:
        """
        Determine pass/fail status.
        Returns None when no grades are available.
        Grade >= 3 → Passed   |   Grade < 3 → Failed
        """
        avg = self.average_grade()
        if avg is None:
            return None
        return avg >= 3.0

    def __str__(self) -> str:
        avg = self.average_grade()
        avg_str = f"{avg:.2f}" if avg is not None else "N/A"
        return (
            f"Student(fn={self._faculty_number}, name={self._name}, "
            f"age={self._age}, avg={avg_str})"
        )


class Teacher(Person):
    def __init__(self, name: str, age: int, subject: str):
        super().__init__(name, age)
        self._subject = subject

    @property
    def subject(self) -> str:
        return self._subject

    def __str__(self) -> str:
        return (
            f"Teacher(name={self._name}, age={self._age}, subject={self._subject})"
        )
class Course:
    def __init__(self, course_id: int, name: str, teacher_name: str = "TBA"):
        self._course_id = course_id
        self._name = name
        self._teacher_name = teacher_name
        self._enrolled_students: list[str] = []  # list of faculty numbers

    @property
    def course_id(self) -> int:
        return self._course_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def teacher_name(self) -> str:
        return self._teacher_name

    def enroll(self, faculty_number: str) -> None:
        if faculty_number not in self._enrolled_students:
            self._enrolled_students.append(faculty_number)

    def enrolled_students(self) -> list[str]:
        return list(self._enrolled_students)

    def __str__(self) -> str:
        return (
            f"Course(id={self._course_id}, name={self._name}, "
            f"teacher={self._teacher_name}, "
            f"enrolled={len(self._enrolled_students)})"
        )