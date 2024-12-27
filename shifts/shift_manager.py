import sqlite3
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import random
import pandas as pd
from tabulate import tabulate

from shifts.logger import ShiftLogger
from shifts.shift_data import EMPLOYEES


@dataclass
class EmployeeState:
    consecutive_home_days: int
    consecutive_shift_days: int
    total_shifts: int
    employee: object
    shift_history: List[datetime.date] = None

    def __post_init__(self):
        self.shift_history = []

    def add_shift(self, date: datetime.date):
        self.shift_history.append(date)
        self.shift_history.sort()

    def current_shift_streak(self) -> int:
        if not self.shift_history:
            return 0

        streak = 1
        for i in range(len(self.shift_history) - 1, 0, -1):
            if (self.shift_history[i] - self.shift_history[i - 1]).days == 1:
                streak += 1
            else:
                break
        return streak


class ScheduleConstraints:
    MIN_HOME_DAYS = 3
    MAX_SHIFT_DAYS = 14
    REQUIRED_SHIFT_SIZE = 8

    @staticmethod
    def check_mandatory_constraints(employee_state: EmployeeState, date: datetime.date) -> bool:
        # Check minimum consecutive home days
        if (employee_state.consecutive_home_days > 0 and
                employee_state.consecutive_home_days < employee_state.employee.min_consecutive_home_days):
            return False

        # Strict enforcement of maximum consecutive shift days
        if (employee_state.consecutive_shift_days >= ScheduleConstraints.MAX_SHIFT_DAYS - 1 or
            employee_state.current_shift_streak() >= ScheduleConstraints.MAX_SHIFT_DAYS - 1):
            return False

        # Check availability and specific home dates
        if not employee_state.employee.is_available(date):
            return False

        return True

    @staticmethod
    def would_exceed_max_shifts(employee_state: EmployeeState, future_dates: int = 1) -> bool:
        return (employee_state.consecutive_shift_days + future_dates > ScheduleConstraints.MAX_SHIFT_DAYS or
                employee_state.current_shift_streak() + future_dates > ScheduleConstraints.MAX_SHIFT_DAYS)



class WeightedConditions:
    def __init__(self, weights: Dict[str, int]):
        self.weights = weights or {
            'consecutive_shift': 7,
            'total_shifts': 8,
            'manager_presence': 9,
            'partner_preference': 6,
            'home_days_balance': 5
        }

    def calculate_score(self, employee_state: EmployeeState, avg_shifts: float) -> float:
        score = 0

        if employee_state.consecutive_shift_days > 5:
            score -= self.weights['consecutive_shift'] * employee_state.consecutive_shift_days

        shift_diff = employee_state.total_shifts - avg_shifts
        if shift_diff > 0:
            score -= self.weights['total_shifts'] * shift_diff

        if employee_state.employee.is_manager:
            score += self.weights['manager_presence']

        if employee_state.employee.preferred_shift_partner:
            score += self.weights['partner_preference']

        return score


class ShiftScheduler:
    def __init__(self, database_path='shift_schedule.db'):
        self.conn = sqlite3.connect(database_path)
        self.employees = {}
        self.logger = ShiftLogger()
        self.create_tables()
        self.logger.info("ShiftScheduler initialized")


    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            constraints_json TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_history (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            period_start DATE,
            period_end DATE,
            days_on_shift INTEGER,
            days_at_home INTEGER,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_schedule (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            shift_date DATE,
            is_on_shift BOOLEAN,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        ''')

        self.conn.commit()

    def add_employee(self, employee):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM employees WHERE name = ?', (employee.name,))
        existing = cursor.fetchone()

        if existing:
            employee._id = existing[0]
            self.employees[employee.name] = employee
            return existing[0]

        constraints_json = json.dumps(employee.to_dict())
        cursor.execute('''
        INSERT INTO employees (name, constraints_json) 
        VALUES (?, ?)
        ''', (employee.name, constraints_json))

        employee_id = cursor.lastrowid
        employee._id = employee_id
        self.employees[employee.name] = employee

        self.conn.commit()
        return employee_id

    def generate_fair_schedule(self, days: int, start_date: datetime.date = None, weights: Dict[str, int] = None) -> \
    Tuple[datetime.date, datetime.date]:
        current_date = start_date or self._get_next_schedule_date()
        end_date = current_date + timedelta(days=days - 1)
        states = self._initialize_employee_states()
        weighted_conditions = WeightedConditions(weights)

        while current_date <= end_date:
            selected = self._select_shift_employees_with_backtracking(current_date, states, weighted_conditions)

            if len(selected) != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                raise RuntimeError(
                    f"Failed to generate valid schedule for {current_date}. Could not satisfy constraints.")

            self._record_shift_assignments(current_date, selected, states)
            current_date += timedelta(days=1)

        self.conn.commit()
        return current_date - timedelta(days=days), end_date

    def generate_fair_schedule(self, days: int, start_date: datetime.date = None, weights: Dict[str, int] = None) -> \
    Tuple[datetime.date, datetime.date]:
        current_date = start_date or self._get_next_schedule_date()
        end_date = current_date + timedelta(days=days - 1)
        states = self._initialize_employee_states()
        weighted_conditions = WeightedConditions(weights)

        while current_date <= end_date:
            selected = self._select_shift_employees_with_backtracking(current_date, states, weighted_conditions)

            if len(selected) != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                raise RuntimeError(
                    f"Failed to generate valid schedule for {current_date}. Could not satisfy constraints.")

            self._record_shift_assignments(current_date, selected, states)
            current_date += timedelta(days=1)

        self.conn.commit()
        return current_date - timedelta(days=days), end_date

    def _select_shift_employees_with_backtracking(self, date: datetime.date, states: Dict[str, EmployeeState],
                                                  weighted_conditions: WeightedConditions, depth: int = 0) -> Set[str]:
        if depth > 100:  # Prevent infinite recursion
            return set()

        available_employees = []
        avg_shifts = sum(state.total_shifts for state in states.values()) / len(states)
        manager_count = 0

        # Get all available employees with their scores
        for name, state in states.items():
            if ScheduleConstraints.check_mandatory_constraints(state, date):
                score = weighted_conditions.calculate_score(state, avg_shifts)
                is_manager = state.employee.is_manager
                if is_manager:
                    manager_count += 1
                available_employees.append((score, name, state, is_manager))

        # Sort by score and manager status
        available_employees.sort(key=lambda x: (-x[0], -x[3]))

        def try_complete_schedule(partial_schedule: Set[str], remaining_employees: List[tuple]) -> Set[str]:
            if len(partial_schedule) == ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                # Verify at least one manager is included
                has_manager = any(states[emp].employee.is_manager for emp in partial_schedule)
                return partial_schedule if has_manager else set()

            if not remaining_employees:
                return set()

            for i, (score, name, state, is_manager) in enumerate(remaining_employees):
                new_schedule = partial_schedule | {name}
                result = try_complete_schedule(
                    new_schedule,
                    remaining_employees[i + 1:]
                )
                if result:
                    return result

            return set()

        # Start with an empty schedule and try to build it
        final_schedule = try_complete_schedule(set(), available_employees)

        if len(final_schedule) != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
            # If we failed to create a valid schedule, try with relaxed constraints
            return self._select_shift_employees_with_relaxed_constraints(date, states, weighted_conditions)

        return final_schedule

    def _select_shift_employees_with_relaxed_constraints(self, date: datetime.date, states: Dict[str, EmployeeState],
                                                         weighted_conditions: WeightedConditions) -> Set[str]:
        """Fallback method with slightly relaxed constraints to ensure we get 8 employees."""
        available_employees = []
        selected = set()

        # First pass: get all eligible employees including those close to limits
        for name, state in states.items():
            if state.employee.is_available(date):  # Only check basic availability
                score = weighted_conditions.calculate_score(state, 0)
                available_employees.append((score, name, state))

        available_employees.sort(reverse=True)

        # Ensure manager presence
        for score, name, state in available_employees:
            if state.employee.is_manager and len(selected) < ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                selected.add(name)
                break

        # Add remaining employees
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected:
                selected.add(name)

        return selected

    def _get_next_schedule_date(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(shift_date) FROM current_schedule')
        last_date = cursor.fetchone()[0]
        return (datetime.strptime(last_date, '%Y-%m-%d').date() + timedelta(days=1)
                if last_date else datetime.now().date() + timedelta(days=1))

    def _initialize_employee_states(self):
        summary = self.get_schedule_summary()
        return {
            name: EmployeeState(
                consecutive_home_days=0,
                consecutive_shift_days=0,
                total_shifts=summary.get(name, {}).get('shifts_until_last', 0),
                employee=emp
            ) for name, emp in self.employees.items()
        }

    def _select_shift_employees(self, date: datetime.date, states: Dict[str, EmployeeState],
                                weighted_conditions: WeightedConditions) -> Set[str]:
        available_employees = []
        avg_shifts = sum(state.total_shifts for state in states.values()) / len(states)

        for name, state in states.items():
            if (ScheduleConstraints.check_mandatory_constraints(state, date) and
                    not ScheduleConstraints.would_exceed_max_shifts(state)):
                score = weighted_conditions.calculate_score(state, avg_shifts)
                available_employees.append((score, name, state))

        available_employees.sort(reverse=True)
        selected = set()

        # Ensure manager presence
        for score, name, state in available_employees:
            if state.employee.is_manager and len(selected) < ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                selected.add(name)
                break

        # Add partner pairs
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected and state.employee.preferred_shift_partner:
                partner = next(
                    (entry for entry in available_employees if entry[1] == state.employee.preferred_shift_partner),
                    None
                )
                if partner and len(selected) <= ScheduleConstraints.REQUIRED_SHIFT_SIZE - 2:
                    selected.update([name, partner[1]])

        # Fill remaining slots while ensuring we don't create future violations
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected:
                selected.add(name)

        return selected

    def _record_shift_assignments(self, date: datetime.date, selected: Set[str], states: Dict[str, EmployeeState]):
        for name, state in states.items():
            is_selected = name in selected
            self._record_schedule_entry(state.employee._id, date, is_selected)

            if is_selected:
                state.consecutive_home_days = 0
                state.consecutive_shift_days += 1
                state.total_shifts += 1
                state.add_shift(date)
            else:
                state.consecutive_home_days += 1
                state.consecutive_shift_days = 0

    def _shift_exists(self, employee_id, date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM current_schedule 
            WHERE employee_id = ? AND shift_date = ?
        ''', (employee_id, date.strftime('%Y-%m-%d')))
        return cursor.fetchone()[0] > 0

    def _record_schedule_entry(self, employee_id, date, is_on_shift):
        if not self._shift_exists(employee_id, date):
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO current_schedule 
                (employee_id, shift_date, is_on_shift) 
                VALUES (?, ?, ?)
            ''', (employee_id, date.strftime('%Y-%m-%d'), is_on_shift))

            employee = next(emp for emp in self.employees.values() if emp._id == employee_id)
            if is_on_shift:
                employee.shift_dates.append(date)
            else:
                employee.home_dates.append(date)
            employee.update_date_counts()

    def _get_schedule_range(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MIN(shift_date), MAX(shift_date) FROM current_schedule')
        start_date_str, end_date_str = cursor.fetchone()
        return (
            datetime.strptime(start_date_str, '%Y-%m-%d').date(),
            datetime.strptime(end_date_str, '%Y-%m-%d').date()
        )

    def _calculate_streak(self, employee_name: str, current_date: datetime.date, is_on_shift: bool) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT shift_date, is_on_shift
            FROM current_schedule cs
            JOIN employees e ON cs.employee_id = e.id
            WHERE e.name = ? AND shift_date <= ?
            ORDER BY shift_date DESC
        ''', (employee_name, current_date.strftime('%Y-%m-%d')))

        streak = 1
        previous_records = cursor.fetchall()

        for i in range(1, len(previous_records)):
            if (previous_records[i][1] == is_on_shift and
                    datetime.strptime(previous_records[i - 1][0], '%Y-%m-%d').date() -
                    datetime.strptime(previous_records[i][0], '%Y-%m-%d').date() == timedelta(days=1)):
                streak += 1
            else:
                break

        return streak

    def verify_schedule_constraints(self, period_start, period_end):
        cursor = self.conn.cursor()
        violations = []

        current_date = period_start
        while current_date <= period_end:
            date_str = current_date.strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT COUNT(*) 
                FROM current_schedule 
                WHERE shift_date = ? AND is_on_shift = 1
            ''', (date_str,))

            shift_count = cursor.fetchone()[0]

            if shift_count < 2:
                violations.append(f"Less than 2 employees on shift on {date_str}")
            if shift_count != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                violations.append(
                    f"Expected {ScheduleConstraints.REQUIRED_SHIFT_SIZE} employees on shift, got {shift_count} on {date_str}")

            current_date += timedelta(days=1)

        return len(violations) == 0, violations

    def parse_hebrew_schedule(self, file_path):
        df = pd.read_excel(file_path)
        date_columns = df.columns[2:]
        home_row = df[df.iloc[:, 1] == "בית"].columns[0]

        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM current_schedule')

        for emp in self.employees.values():
            emp.shift_dates = []
            emp.home_dates = []
            emp.total_shifts_days = 0
            emp.total_home_days = 0

        hebrew_to_employee = {}
        for emp in self.employees.values():
            for hebrew_name in emp.hebrew_names:
                hebrew_to_employee[hebrew_name] = emp

        for col in date_columns:
            date_str = str(col).strip()
            if '.' in date_str:
                day, month = map(int, date_str.split('.'))
                year = datetime.now().year
                if month < datetime.now().month:
                    year += 1
                current_date = datetime(year, month, day).date()

                shift_employees = df.iloc[:home_row - 3, df.columns.get_loc(col)]
                shift_employees = shift_employees.dropna().tolist()

                home_employees = df.iloc[home_row - 1:30, df.columns.get_loc(col)]
                home_employees = home_employees.dropna().tolist()

                processed_employees = set()

                for hebrew_name in shift_employees:
                    if hebrew_name in hebrew_to_employee:
                        employee = hebrew_to_employee[hebrew_name]
                        if employee.name not in processed_employees:
                            self._record_schedule_entry(employee._id, current_date, True)
                            processed_employees.add(employee.name)

                for hebrew_name in home_employees:
                    if hebrew_name in hebrew_to_employee:
                        employee = hebrew_to_employee[hebrew_name]
                        if employee.name not in processed_employees:
                            self._record_schedule_entry(employee._id, current_date, False)
                            processed_employees.add(employee.name)

        self.conn.commit()

    def print_daily_schedule(self, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        if not start_date or not end_date:
            start_date, end_date = self._get_schedule_range()

        table_data = []
        current_date = start_date

        while current_date <= end_date:
            shift_emps = []
            home_emps = []

            cursor.execute('''
                SELECT e.name, cs.is_on_shift, e.constraints_json
                FROM current_schedule cs
                JOIN employees e ON cs.employee_id = e.id
                WHERE cs.shift_date = ?
            ''', (current_date.strftime('%Y-%m-%d'),))

            for name, is_on_shift, constraints in cursor.fetchall():
                emp_info = json.loads(constraints)
                prefix = '*' if emp_info.get('is_manager') else ''
                streak = self._calculate_streak(name, current_date, is_on_shift)
                emp_str = f"{prefix}{name} ({streak}d)"

                if is_on_shift:
                    shift_emps.append((emp_info.get('is_manager', False), streak, emp_str))
                else:
                    home_emps.append((emp_info.get('is_manager', False), streak, emp_str))

            # Sort employees: managers first, then by streak length
            shift_emps.sort(key=lambda x: (-x[0], -x[1]))
            home_emps.sort(key=lambda x: (-x[0], -x[1]))

            table_data.append([
                current_date.strftime('%d/%m/%Y'),
                '\n'.join(emp[2] for emp in shift_emps),
                '\n'.join(emp[2] for emp in home_emps)
            ])

            current_date += timedelta(days=1)

        self.logger.info(f"\nDaily Schedule for {start_date} -> {end_date}:")
        headers = ['Date', 'On Shift', 'At Home']
        self.logger.info(tabulate(table_data, headers=headers, tablefmt='grid'))
        self.logger.info("\n")

    def get_schedule_summary(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, constraints_json FROM employees')
        employees = cursor.fetchall()
        summary = {}

        for emp_id, name, _ in employees:
            cursor.execute('''
                SELECT shift_date, is_on_shift
                FROM current_schedule
                WHERE employee_id = ?
                ORDER BY shift_date
            ''', (emp_id,))
            schedule = cursor.fetchall()

            shift_dates = [date for date, is_shift in schedule if is_shift]
            home_dates = [date for date, is_shift in schedule if not is_shift]

            cursor.execute('SELECT MAX(shift_date) FROM current_schedule')
            last_date = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*)
                FROM current_schedule
                WHERE employee_id = ? 
                AND is_on_shift = 1
                AND shift_date <= ?
            ''', (emp_id, last_date))
            shifts_until_last = cursor.fetchone()[0]

            summary[name] = {
                'shift_dates': shift_dates,
                'home_dates': home_dates,
                'total_shifts': len(shift_dates),
                'total_home_days': len(home_dates),
                'shifts_until_last': shifts_until_last
            }

        return summary

    def print_employee_summary(self):
        def format_date(date):
            return datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m') if isinstance(date, str) else date.strftime(
                '%d/%m')

        def get_date_ranges(dates):
            if not dates:
                return []

            dates = sorted(dates)
            ranges = []
            start = end = dates[0]
            current_count = 1

            for date in dates[1:]:
                curr_date = datetime.strptime(date, '%Y-%m-%d').date() if isinstance(date, str) else date
                prev_date = datetime.strptime(end, '%Y-%m-%d').date() if isinstance(end, str) else end

                if curr_date - prev_date > timedelta(days=1):
                    if current_count == 1:
                        ranges.append(f"{format_date(start)} (1d)")
                    else:
                        ranges.append(f"{format_date(start)}-{format_date(end)} ({current_count}d)")
                    start = date
                    current_count = 1
                else:
                    current_count += 1
                end = date

            if current_count == 1:
                ranges.append(f"{format_date(start)} (1d)")
            else:
                ranges.append(f"{format_date(start)}-{format_date(end)} ({current_count}d)")
            return ranges

        table_data = []
        for name, emp in self.employees.items():
            all_dates = [(date, True) for date in emp.shift_dates] + [(date, False) for date in emp.home_dates]
            all_dates.sort()

            current_streak = ""
            if all_dates:
                last_date, is_shift = all_dates[-1]
                streak_count = 1
                for i in range(len(all_dates) - 2, -1, -1):
                    curr_date = datetime.strptime(all_dates[i][0], '%Y-%m-%d').date() if isinstance(all_dates[i][0],
                                                                                                    str) else \
                    all_dates[i][0]
                    next_date = datetime.strptime(all_dates[i + 1][0], '%Y-%m-%d').date() if isinstance(
                        all_dates[i + 1][0], str) else all_dates[i + 1][0]

                    if all_dates[i][1] == is_shift and next_date - curr_date == timedelta(days=1):
                        streak_count += 1
                    else:
                        break
                current_streak = f"({streak_count}d at {'shift' if is_shift else 'home'})"

            row = [
                name,
                emp.total_shifts_days,
                emp.total_home_days,
                current_streak,
                '\n'.join(get_date_ranges(emp.shift_dates)),
                '\n'.join(get_date_ranges(emp.home_dates))
            ]
            table_data.append(row)

        headers = ['Employee', 'Days at Shift', 'Days at Home', 'Current Streak', 'Shift Periods', 'Home Periods']
        self.logger.info("\nEmployee Schedule Summary:")
        self.logger.info(tabulate(table_data, headers=headers, tablefmt='grid', numalign='right'))
        self.logger.info("\n")

    def close(self):
        self.conn.close()


def main():
    scheduler = ShiftScheduler()
    for employee in EMPLOYEES:
        scheduler.add_employee(employee)

    scheduler.parse_hebrew_schedule("Syria 25 Team Maslow.xlsx")
    scheduler.print_daily_schedule()
    scheduler.print_employee_summary()

    start_date, end_date = scheduler.generate_fair_schedule(days=14)
    scheduler.print_daily_schedule(start_date, end_date)
    scheduler.print_employee_summary()
    scheduler.close()


if __name__ == '__main__':
    main()